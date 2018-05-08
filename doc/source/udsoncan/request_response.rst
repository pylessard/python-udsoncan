Request and Response
====================

Messages exchanged by the client and the server a represented by a ``Request`` and a ``Response``. 

The client sends ``Requests`` to the server that include a service number, an optional subfunction and some data. The server process the request and answer with a ``Response`` that contains an echo of the service number, a response code and some additional data.

The following classes provides the encessary interface to manipulates UDS requests and responses.

------

.. _Request:

Request
-------

.. code-block:: python
   
   req = Request(service=ECUReset, subfunction=1, data=b'\x99\x88')
   payload = req.get_payload()
   print(payload) # b'\x11\x01\x99\x88'
   req2 = Request.from_payload(payload)
   print(req2) # <Request: [ECUReset] (subfunction=1) - 2 data bytes at 0x12345678>

.. autoclass:: udsoncan.Request
.. automethod:: udsoncan.Request.get_payload
.. automethod:: udsoncan.Request.from_payload

.. _Response:

--------

Response
---------

.. code-block:: python
   
   response = Response(service=ECUReset, code=Response.Code.PositiveResponse, data=b'\x11\x22')
   payload = response.get_payload()
   print(payload) # b'\x51\x11\x22'
   response2 = Response.from_payload(payload)
   print(response2) # <PositiveResponse: [ECUReset] - 2 data bytes at 0x7f9367e619b0>

.. autoclass:: udsoncan.Response
.. automethod:: udsoncan.Response.get_payload
.. automethod:: udsoncan.Response.from_payload

Response Codes
##############

.. autoclass:: udsoncan::Response.Code
   :members: 
   :undoc-members:
   :member-order: bysource