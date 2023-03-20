Request and Response
====================

Messages exchanged by the client and the server are represented by a ``Request`` and a ``Response``. 

The client sends ``Requests`` to the server that include a service number, an optional subfunction and some data. The server processes the request and answers with a ``Response`` that contains an echo of the service number, a response code and some additional data.

The following classes provides the necessary interface to manipulate UDS requests and responses.

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
    :noindex:
.. automethod:: udsoncan.Request.from_payload
    :noindex:

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
    :members: 
.. automethod:: udsoncan.Response.get_payload
    :noindex:
.. automethod:: udsoncan.Response.from_payload
    :noindex:

Response Codes
##############

.. autoclass:: udsoncan::Response.Code
    :members: 
    :undoc-members:
    :member-order: bysource
    :exclude-members: get_name, is_negative, is_supported_by_standard
