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

How reliable is this code?
--------------------------

.. epigraph::
   
   To the best of my knowledge, quite good. This project comes with a fair amount of unit tests, many based on examples proposed in the UDS standard document.
   Every service encoding/decoding is unit-tested.
   
   Only few common services have been tested on a real ECU.

Why is there unimplemented services?
------------------------------------

.. epigraph::
   
   One of these reasons

      - The actual synchronous client doesn't support it.
      - The ratio of "service usage in the industry" over "the amount of work necessary to implement it" is too poor.

   As for the client capabilities, I am aware that the single-request/single-response mechanism is limiting. I believe it is enough to handle the majority of today's use-case. 
   I may work in a future version for a more sophisticated client that have a message queue for each service, therefore allowing asynchronous services such as :ref:`ResponseOnEvent<ResponseOnEvent>` or :ref:`ReadDataByPeriodicIdentifier<ReadDataByPeriodicIdentifier>`

---------------------------------------------------

What is the DTC mirror memory?
------------------------------

.. epigraph::



What makes a DTC permanent?
---------------------------

.. epigraph::
