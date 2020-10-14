# HL7 MLLP Pong 🏓

MLLP pong is a simple MLLP server for you to test your MLLP integrations. Since you're probably already suffering, this image is as simple as possible for you to make integration tests. 

# How to use
In this server you will have multiple servers that will reply differently to your requests. Depending on what you want to test, use the following ports:

```
docker build -t mllp-pong .

docker run -p 666:666 -p 1337:1337 mllp-pong
```

### 👍 ACK server (port 1337)
This server will reply with an ack as long as the message sent is valid

### 👹 Chaos server (port 666)
This server will reply with an HL7 Internal server error no matter what you do or send

### Note about invalid messages
Because the error messages are sent via an ACK message, which requires a valid MSH (message header segment), if you send gibberish you will get an error message that looks like HL7 but is not a valid HL7 message (does not have all the mandatory fields).