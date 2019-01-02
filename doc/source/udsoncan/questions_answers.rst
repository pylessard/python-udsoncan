Questions and answers
=====================

What version of the standard has been used?
-------------------------------------------

.. epigraph::
   
   ISO-14229:2006, which is the document that I had access to when writing the code.

Can we expect an update for the 2013 version?
---------------------------------------------

.. epigraph::
   
   Yes, one day, when I'll put my hands on the 2013 document. 
   Access to ISO standard costs money and this project is 100% voluntary.

-----

How reliable is this code?
--------------------------

.. epigraph::
   
   To the best of my knowledge, quite good. This project comes with a fair amount of unit tests, many based on examples proposed in the UDS standard document.
   Every service encoding/decoding is unit-tested.
   
   Only a few common services have been tested on a real ECU.

-----

Why is there unimplemented services?
------------------------------------

.. epigraph::
   
   One of these reasons:

      - The actual synchronous client doesn't support it.
      - The ratio of "service usage in the industry" over "the amount of work necessary to implement it" is too poor.

   As for the client capabilities, I am aware that the single-request/single-response mechanism of the actual client is limiting. I believe it is enough to handle the majority of today's use-cases. 
   I may work in a future version for a more sophisticated client that will have message queues for each service with callback and everything, therefore allowing asynchronous services such as :ref:`ResponseOnEvent<ResponseOnEvent>` or :ref:`ReadDataByPeriodicIdentifier<ReadDataByPeriodicIdentifier>`

-----

I have a CAN transceiver, how do I use this project now?
--------------------------------------------------------

.. epigraph::

   This project is not all you need; you need to create a path for the data to reach your CAN box.

   Under Linux, if your CAN box is supported by SocketCAN, you should have a new network interface after plugging in the device. Compile and install `this module <https://github.com/hartkopp/can-isotp>`_, then find out what CAN IDs are used for diagnostics and use the :class:`SocketConnection<udsoncan.connections.SocketConnection>` or :class:`IsoTPSocketConnection<udsoncan.connections.IsoTPSocketConnection>`

   If you do not want to rely on SocketCAN, you can use :class:`PythonIsoTpConnection<udsoncan.connections.PythonIsoTpConnection>`. This connection will make usage of  Python's `can-isotp <https://can-isotp.readthedocs.io>`_ module which can be coupled with `python-can <https://python-can.readthedocs.io>`_ to access the CAN layer. The main advantage of doing this is that python-can supports many can interface, both under Windows and Linux. Unfortunately, the transport layer (IsoTp) implementation needs to be in the user space, which usually fails to meet the protocol timing requirements. Most of time, this is not an issue.

   If you can't use any of the above solution, you will need to write your own Connection class that handles everything from the transport protocol (IsoTP) to the hardware which means interacting with the drivers. See :ref:`Defining a new Connection<DefiningNewConnection>`

-----

What is the DTC mirror memory?
------------------------------

.. epigraph::
   
   A mirror memory is an optional feature that a UDS server can offer. It's a snapshot of a specific memory section that is frozen in time. Interacting with this *mirror memory* avoids race conditions such as a DTC status changing while reading its value.

   The client may ask the server to copy the mirror memory or erase it by calling a routine or writing a data identifier. The implementation is ECU manufacturer specific.

-----

What makes a DTC permanent?
---------------------------

.. epigraph::
   
   Some diagnostic trouble codes are severe and can only be removed by the manufacturer. A permanent DTC is stored in a non-volatile memory and cannot be cleared with a common test tool or by removing power on the ECU.

-----

How can I contribute?
---------------------

Create a Github issue, fork the project, propose a pull request and I will review it; that's the best way.