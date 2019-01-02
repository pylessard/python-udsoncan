Introduction to UDS
===================

The Unified Diagnostic Services (UDS) standard also known as ISO-14229 is an application protocol interface used in road vehicles for diagnostics, debugging and configuration of ECUs.

UDS defines how messages should be formatted but not how they should be implemented (although the standard suggests some good practices); that's why it is an interface. 

The UDS client is usually a tester unit meant to be connected to a vehicle diagnostic port. The UDS server is usually a device within the vehicle that is connected to the CAN bus (accessible by the diagnostic port). This device is referred to as an Electronic Control Unit (ECU). 

Services
--------

Each functionality of the standard is grouped within the concept of a **service**. A service is basically a type of request that has some parameters. Here's some examples of how functionalities are grouped within services : 

 - Reading the Diagnostic Trouble Codes known as DTCs (:ref:`ReadDTCInformation <ReadDTCInformation>`)
 - Setting vehicle-specific configuration (:ref:`WriteDataByIdentifier <WriteDataByIdentifier>`)
 - Overriding IOs (:ref:`InputOutputControlByIdentifier <InputOutputControlByIdentifier>`)
 - Requesting a reset (:ref:`ECUReset <ECUReset>`)
 - Etc.

These services can have subfunctions that are specific to them. For instance, the :ref:`ECUReset <ECUReset>` service has a subfunction that describes the type of reset that the client wants to perform. It can be a hard reset (power cycle) or a soft reset (restarting the firmware). The subfunction is the first byte of the service payload and its value is defined by UDS. The way the server triggers a reset is not defined by UDS and is left to the discretion of the server programmer.

Sessions and security levels
----------------------------

When connecting to a server, the client has a session and a security level. 

By default, the server greets a new client by assigning it the "default session" in which only a few specific services are accessible like reading the DTCs. UDS defines 4 sessions types but defines the list of available services only for the default session. In other words, the ECU manufacturer decides what services are available for each session, excluding the default session. A client may switch to any session without restrictions (with the :ref:`DiagnosticSessionControl <DiagnosticSessionControl>` service), it is not a security mechanism. The ECU manufacturer can define 32 additional sessions.

The security level is a status that the client gains by unlocking features within the server by providing a security key. UDS is designed to allow up to 64 security levels that are, in the end, boolean flags set in the server. These security levels, as well as what they unlock, are not defined by UDS but will be by the ECU manufacturer. A security level can unlock a whole service, a subfunction or the access to a specific value. For instance, writing the Vehicle Identification Number (VIN) may require a specific security level that is different from what is needed to write the maximum speed or override the vehicle IOs.

Unlocking security levels is not allowed in the default session. To gain some privileges, the client must first switch to a non-default session that enables the :ref:`SecurityAccess <SecurityAccess>` service. Only then may the client execute the handshake that will unlock the wanted feature. Usually, when privileges are gained, they will expire after a short period of time defined by the ECU manufacturer. A keepalive message will keep the security level unlocked and the session active; these keepalive messages are sent with service :ref:`TesterPresent <TesterPresent>`

Security algorithm
------------------

The payload that must be sent to unlock a security level is not defined by UDS; UDS defines how to proceed with the key exchange. This process consists of 2 exchanges of request/response between the client and the server. It goes as follows:

 1. First, the client requests for a **seed** to unlock a specific security level (identified by a number). This seed is usually a random value that the client must use in order to compute the key. It is meant to prevent someone from recording the CAN bus message exchange and then gaining privileges by blindly sending what was recorded. In cryptography terms, the seed is a nonce used to avoid replay attacks.
 2. Once the client gets the seed, it must **compute a key** using an algorithm that is defined by the ECU manufacturer and known by the server.
 3. The client then sends the **key** to the server, the server verifies it and, if it matches the server's value, the security level is unlocked and a positive message is responded to the client.

 The security algorithm can be any algorithm. The lack of algorithm definition in the UDS standard leaves some room for good security design, but also for poor design - it's up to the manufacturer. Yes, some manufacturers implement security through obscurity while some others will go for a more robust pre-shared key scheme.
