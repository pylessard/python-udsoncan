Examples
========

.. _layer_of_intelligneces:

Different layers of intelligence (1 to 4)
-----------------------------------------

In the following examples, we will request an ECU reset in 4 different ways. We will start by crafting a binary payload manually, then we will add a layer of interpretation making the code more comprehensive each time. 

1. Raw Connection
#################

.. code-block:: python

   my_connection.send(b'\x11\x01\x77\x88\x99') # Sends ECU Reset, with subfunction = 1
   payload = my_connection.wait_frame(timeout=1)
   if payload == b'\x51\x01':
      print('Success!')
   else:
      print('Reset failed')

2. Request and Responses
########################

.. code-block:: python

   req = Request(services.ECUReset, subfunction=1, data=b'\x77\x88\x99')
   my_connection.send(req.get_payload()) 
   payload = my_connection.wait_frame(timeout=1)
   response = Response.from_payload(payload)
   if response.service == service.ECUReset and response.code == Response.Code.PositiveResponse and response.data == b'\x01':
      print('Success!')
   else:
      print('Reset failed')

3. Services
###########

.. code-block:: python

   req = services.ECUReset.make_request(reset_type=1, data=b'\x77\x88\x99')
   my_connection.send(req.get_payload()) 
   payload = my_connection.wait_frame(timeout=1)
   response = Response.from_payload(payload)
   services.ECUReset.interpret_response(response)
   if response.service == service.ECUReset and response.code == Response.Code.PositiveResponse and response.service_data.reset_type_echo == 1:
      print('Success!')
   else:
      print('Reset failed')

4. Client
#########

.. code-block:: python

   try:
      client.ecu_reset(reset_type=1, data=b'\x77\x88\x99')
      print('Success!')
   except:
      print('Reset failed')

-----

.. _example_using_python_can:

Using UDS over python-can
-------------------------

In this example, we show how to use :class:`PythonIsoTpConnection<udsoncan.connections.PythonIsoTpConnection>` with a fictive Vector interface.
Note that, in order to run this code, both ``python-can`` and ``can-isotp`` must be installed.

.. code-block:: python

   from can.interfaces.vector import VectorBus
   from udsoncan.connections import PythonIsoTpConnection
   from udsoncan.client import Client
   import isotp

   # Refer to isotp documentation for full details about parameters
   isotp_params = {
      'stmin' : 32,                          # Will request the sender to wait 32ms between consecutive frame. 0-127ms or 100-900ns with values from 0xF1-0xF9
      'blocksize' : 8,                       # Request the sender to send 8 consecutives frames before sending a new flow control message
      'wftmax' : 0,                          # Number of wait frame allowed before triggering an error
      'tx_data_length ' : 8,                 # Link layer (CAN layer) works with 8 byte payload (CAN 2.0)
      'tx_data_min_length  ' : None,         # Minimum length of CAN messages. When different from None, messages are padded to meet this length. Works with CAN 2.0 and CAN FD.
      'tx_padding' : 0,                      # Will pad all transmitted CAN messages with byte 0x00. 
      'rx_flowcontrol_timeout' : 1000,       # Triggers a timeout if a flow control is awaited for more than 1000 milliseconds
      'rx_consecutive_frame_timeout' : 1000, # Triggers a timeout if a consecutive frame is awaited for more than 1000 milliseconds
      'squash_stmin_requirement' : False,    # When sending, respect the stmin requirement of the receiver. If set to True, go as fast as possible.
      'max_frame_size ' : 4095               # Limit the size of receive frame.
   }

   bus = VectorBus(channel=0, bitrate=500000)                                          # Link Layer (CAN protocol)
   tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x123, rxid=0x456) # Network layer addressing scheme
   stack = isotp.CanStack(bus=bus, address=tp_addr, params=isotp_params)               # Network/Transport layer (IsoTP protocol)
   conn = PythonIsoTpConnection(stack)                                                 # interface between Application and Transport layer
   with Client(conn, request_timeout=1) as client:                                     # Application layer (UDS protocol)
      client.change_session(1)   
      # ...

-----

.. _example_default_memloc_format:

Server default address and size format
--------------------------------------

In this example, we show how the :ref:`Client<Client>` uses the memory location format configurations.

.. code-block:: python

   client.config['server_address_format'] = 16
   client.config['server_memorysize_format'] = 8
   # Explicit declaration. Client will used this value
   memloc1 = MemoryLocation(address=0x1234, memorysize=0x10, address_format=16, address_format=8)
   # No explicit declaration. Client will use the default values in the configuration
   memloc2 = MemoryLocation(address=0x1234, memorysize=0x10)
   response = client.read_memory_by_address(memloc1)
   response = client.read_memory_by_address(memloc2)

-----

.. _example_security_algo:

Security algorithm implementation
---------------------------------

   The following example shows how to define a security algorithm in the client configuration. The algorithm XOR the seed with a pre-shared key passed as a parameter.

.. code-block:: python

   def myalgo(level, seed, params):
   """
   Builds the security key to unlock a security level. Returns the seed xor'ed with pre-shared key.
   """
      output_key = bytearray(seed)
      xorkey = bytearray(params['xorkey'])

      for i in range(len(seed)):
         output_key[i] = seed[i] ^ xorkey[i%len(xorkey)]
      return bytes(output_key)

   client.config['security_algo'] = myalgo
   client.config['security_algo_params'] = dict(xorkey=b'\x12\x34\x56\x78')

.. warning:: This algorithm is not secure and is given as an example only because of its simple implementation. XOR encryption is weak on many levels; it is vulnerable to known-plaintext attacks, relatively weak against replay attacks and does not provide enough diffusion (pattern recognition is possible). If you are an ECU programmer, please **do not implement this**.

-----


.. _reading_a_did:

Reading a DID with ReadDataByIdentifier
---------------------------------------

This example shows how to configure the client with a DID configuration and request the server with ReadDataByIdentifier

.. code-block:: python

   import udsoncan
   from udsoncan.connections import IsoTPSocketConnection
   from udsoncan.client import Client
   import udsoncan.configs

   class MyCustomCodecThatShiftBy4(udsoncan.DidCodec):
      def encode(self, val):
         val = (val << 4) & 0xFFFFFFFF # Do some stuff
         return struct.pack('<L', val) # Little endian, 32 bit value

      def decode(self, payload):
         val = struct.unpack('<L', payload)[0]  # decode the 32 bits value
         return val >> 4                        # Do some stuff (reversed)

      def __len__(self):
         return 4    # encoded paylaod is 4 byte long.


   config = dict(udsoncan.configs.default_client_config)
   config['data_identifiers'] = {
      0x1234 : MyCustomCodecThatShiftBy4,    # Uses own custom defined codec. Giving the class is ok
      0x1235 : MyCustomCodecThatShiftBy4(),  # Same as 0x1234, giving an instance is good also
      0xF190 : udsoncan.AsciiCodec(15)       # Codec that read ASCII string. We must tell the length of the string
      }

   # IsoTPSocketconnection only works with SocketCAN under Linux. Use another connection if needed.
   conn = IsoTPSocketConnection('vcan0', rxid=0x123, txid=0x456)  
   with Client(conn,  request_timeout=2, config=config) as client:
      response = client.read_data_by_identifier(0xF190)
      print(response.service_data.values[0xF190]) # This is a dict of DID:Value
      
      # Or, if a single DID is expected, a shortcut to read the value of the first DID
      vin = client.read_data_by_identifier_first(0xF190)     
      print(vin)  # 'ABCDE0123456789' (15 chars)

-----

.. _iocontrol_composite_did:

InputOutputControlByIdentifier Composite DID
--------------------------------------------

This example shows how the InputOutputControlByIdentifier can be used with a composite data identifier and how to build a proper `ioconfig` dict which can be tricky.
The example shown below correspond to a real example provided in ISO-14229 document

.. code-block:: python

   # Example taken from UDS standard

   class MyCompositeDidCodec(DidCodec):
      def encode(self, IAC_pintle, rpm, pedalA, pedalB, EGR_duty):
         pedal = (pedalA << 4) | pedalB
         return struct.pack('>BHBB', IAC_pintle, rpm, pedal, EGR_duty)

      def decode(self, payload):
         vals = struct.unpack('>BHBB', payload)
         return {
            'IAC_pintle': vals[0],
            'rpm'       : vals[1],
            'pedalA'    : (vals[2] >> 4) & 0xF,
            'pedalB'    : vals[2] & 0xF,
            'EGR_duty'  : vals[3]
         }

      def __len__(self):
         return 5    

   ioconfig = {
         0x132 : MyDidCodec,
         0x456 : '<HH',
         0x155 : {
            'codec' : MyCompositeDidCodec,
            'mask' : {
               'IAC_pintle': 0x80,
               'rpm'       : 0x40,
               'pedalA'    : 0x20,
               'pedalB'    : 0x10,
               'EGR_duty'  : 0x08
            },
            'mask_size' : 2 # Mask encoded over 2 bytes
         }
      }

      values = {'IAC_pintle': 0x07, 'rpm': 0x1234, 'pedalA': 0x4, 'pedalB' : 0x5,  'EGR_duty': 0x99}
      req = InputOutputControlByIdentifier.make_request(0x155, values=values, masks=['IAC_pintle', 'pedalA'], ioconfig=ioconfig)

.. _example_using_j2534:

Using J2534 PassThru Interface
-------------------------

This is an example for how to use :class:`J2534Connection<udsoncan.connections.J2534Connection>`.
This connection *requires* a compatible J2534 PassThru device (such as a tactrix openport 2.0 cable), with a DLL for said device installed.
Note, this conncection has been written to plug in where a standard IsoTPSocketConncetion had been used (i.e. code ported from Linux to Windows).  Functionality, from a high level, is identical.

.. code-block:: python

   from udsoncan.connections import J2534Connection
   
   conn = J2434Connection(windll='C:\Program Files (x86)\OpenECU\OpenPort 2.0\drivers\openport 2.0\op20pt32.dll',
           rxid=0x7E8, txid=0x7E0)                                                     # Define the connection using the absolute path to the DLL, rxid and txid's for isotp
           
   conn.send(b'\x22\xf2\x00')                                                          # Mode 22 request for DID F200
   response = conn.wait_frame()                                                        # response should = 0x62 F2 00 data data data data
   
   with Client(conn, request_timeout=1) as client:                                     # Application layer (UDS protocol)
      client.change_session(1)   
      # ...

-----
