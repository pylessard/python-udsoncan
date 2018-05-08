Questions and answers
=====================

What version of the standard has been used?
-------------------------------------------

.. epigraph::
   
   ISO-14229:2006, which is the document that I had access to when writing the code.

Can we expect an update for the 2013 version?
---------------------------------------------

.. epigraph::
   
   Yes, one day, when I'll put my hand on the 2013 document. 
   Access to ISO standard cost money and this project is 100% voluntary.

-----

How reliable is this code?
--------------------------

.. epigraph::
   
   To the best of my knowledge, quite good. This project comes with a fair amount of unit tests, many based on examples proposed in the UDS standard document.
   Every service encoding/decoding is unit-tested.
   
   Only few common services have been tested on a real ECU.

-----

Why is there unimplemented services?
------------------------------------

.. epigraph::
   
   One of these reasons

      - The actual synchronous client doesn't support it.
      - The ratio of "service usage in the industry" over "the amount of work necessary to implement it" is too poor.

   As for the client capabilities, I am aware that the single-request/single-response mechanism of the actual client is limiting. I believe it is enough to handle the majority of today's use-case. 
   I may work in a future version for a more sophisticated client that will have message queues for each service with callback and everything, therefore allowing asynchronous services such as :ref:`ResponseOnEvent<ResponseOnEvent>` or :ref:`ReadDataByPeriodicIdentifier<ReadDataByPeriodicIdentifier>`

-----

I have a CAN transceiver, how do I use this project now?
--------------------------------------------------------

.. epigraph::

   This project is not all you need, you need to create path for the data to reach your CAN box.

   Under Linux, if your CAN box is supported by SocketCAN, you should have a new network interface after plugging the device. Compile and install `this module <https://github.com/hartkopp/can-isotp>`_, then find what are the CAN ID used for diagnostic and use the :class:`SocketConnection<udsoncan.connections.SocketConnection>` or :class:`IsoTPConnection<udsoncan.connections.IsoTPConnection>`

   If you don't have the above privilege, you will need to write you own Connection class that handles everything from the transport protocol (IsoTP) to the hardware which means interracting with the drivers. 

   Note that for windows user, Peak-System Technik Gmbh provides a DLL to handle the IsoTP protocol.

-----

What is the DTC mirror memory?
------------------------------

.. epigraph::
   
   A mirror memory is an optional feature that a UDS server can offer. It's a snapshot of a specific memory section that is frozen in time. Interracting with this *mirror memory* avoid race conditions such as a DTC status changing while reading its value.

   The client may ask the server to copy the mirror memory or erase it by calling a routine or writing a data identifier. The implementation is ECU manufacturer specific.

-----

What makes a DTC permanent?
---------------------------

.. epigraph::
   
   Some diagnostic trouble code are severe and can only be removed by the manufacturer. A permanent DTC is stored in a non-volatile memory and cannot be cleared with a common test tool or by removing power on the ECU.

-----

How can I contribute?
---------------------

Create a Github issue, fork the project, propose a pull request and I will review it; that's the best way.