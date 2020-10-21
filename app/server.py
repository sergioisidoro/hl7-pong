import logging
import threading
from collections import defaultdict

from hl7apy.core import Message
from hl7apy.exceptions import ValidationError
from hl7apy.mllp import (MLLPServer, AbstractHandler, AbstractErrorHandler,
                         UnsupportedMessageType, InvalidHL7Message)
from hl7apy.parser import parse_message


def last_ditch_error_mssage(exception):
    m = Message("ACK")
    m.msh.msh_9 = "ACK^^ACK"
    m.msa.msa_1 = "AR"
    m.err.err_3 = "207"
    # E - Error, F - Fatal, I- Information, W - Warning
    m.err.err_4 = "%s" % "F"
    m.err.err_8 = "Cannot create valid error resp without a valid request header! %s" % exception
    return m.to_mllp()

class ErrorHandler(AbstractErrorHandler):
    """
    ErrorHandler will send an NACK with the exception as the error message.
    """
    def reply(self):
        logging.info("Handling message with ErrorHandler")
        # ERROR CODES:
        # https://hl7-definition.caristix.com/v2/HL7v2.7/Tables/0357

        if isinstance(self.exc, UnsupportedMessageType):
            err_code = 200  # Unsupported message type
            err_msg = 'Unsupported message: %s' % self.exc
        elif isinstance(self.exc, InvalidHL7Message):
            err_code = 100
            err_msg = 'Invalid: %s' % self.exc
        else:
            err_code = 207  # Application internal error
            err_msg = 'Unknown error occurred: %s' % self.exc

        try:
            parsed_message = parse_message(self.incoming_message)
            parsed_message.MSH.validate()
            m = Message("ACK")
            message_type = "ACK^%s^ACK" % parsed_message.msh.msh_9.msh_9_2.value
            m.msh.msh_9 = message_type
            m.msa.msa_1 = "AR"
            m.msa.msa_2 = parsed_message.MSH.MSH_10
            m.msh.msh_10 = parsed_message.msh.msh_10
            m.msh.msh_11 = parsed_message.msh.msh_11
            m.msh.msh_12 = parsed_message.msh.msh_12.value

            m.err.err_3 = "%s" % err_code
            # E - Error, F- Fatal, I- Information, W - Warning
            m.err.err_4 = "%s" % "E"

            m.err.err_8 = "%s" % err_msg
            assert m.validate()
            return m.to_mllp()
        except Exception as e:
            logging.warning("Cannot build valid error message. %s" % e)
            return last_ditch_error_mssage(e)


class AckAllHandler(AbstractHandler):
    """
    The AckAllHandler will reply ok to everything as long as
    the message is valid.
    """
    def reply(self):
        logging.info("Handling message with AckAllHandler")
        incoming_msg = parse_message(self.incoming_message)
        try:
            incoming_msg.validate()
            res = Message('ACK')
            # Create a message type with the trigger event
            message_type = "ACK^%s^ACK" % incoming_msg.msh.msh_9.msh_9_2.value
            res.msh.msh_9 = message_type

            res.msh.msh_10 = incoming_msg.msh.msh_10.value
            res.msh.msh_11 = incoming_msg.msh.msh_11.value
            res.msh.msh_12 = incoming_msg.msh.msh_12.value

            res.msa.msa_1 = "AA"
            res.msa.msa_2 = incoming_msg.msh.msh_10.value
            res.msa.msa_3 = "Wow, such message, very valid, Wow!"

            logging.info("replying with %s" % [res.to_mllp()])
            return res.to_mllp()
        except ValidationError:
            raise InvalidHL7Message


class ChaosHandler(AbstractHandler):
    """
    Chaos handler will always return a internal server error.
    """
    def reply(self):
        logging.info("Handling message with ChaosHandler")
        raise RuntimeError("Eeeevil!")


chaos_handler = defaultdict(lambda: (ChaosHandler,))
chaos_handler["ERR"] = (ErrorHandler,)

ack_all_handlers = defaultdict(lambda: (AckAllHandler,))
ack_all_handlers["ERR"] = (ErrorHandler,)


def spin_server_tread(server, thread_name):
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.name = thread_name

    server_thread.start()
    logging.info("Server loop running in thread: %s" % thread_name)
    return server_thread


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("STARTING MLLP PONG SERVER 🏓")
    logging.info("---")

    logging.info("👹 STARTING CHAOS HANDLER ON PORT 666 - THREAD")
    chaos_server = MLLPServer('0.0.0.0', 666, chaos_handler)
    spin_server_tread(chaos_server, "CHAOS")

    logging.info("👍 STARTING ALLWAYS ACK SERVER ON PORT 1337 - MAIN process")
    server = MLLPServer('0.0.0.0', 1337, ack_all_handlers)
    server.serve_forever()
