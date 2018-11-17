Examples
========

.. _layer_of_intelligneces:

Different layers of intelligence
--------------------------------

In the following examples, we will request an ECU reset in 4 different ways. We will start by crafting a binary payload manually, then we will add a layer of interpretation making the code more comprehensive each time. 

Raw Connection
##############

.. code-block:: python

   my_connection.send(b'\x11\x01\x77\x88\x99') # Sends ECU Reset, with subfunction = 1
   payload = my_connection.wait_frame(timeout=1)
   if payload == b'\x51\x01':
      print('Success!')
   else:
      print('Reset failed')

Request and Responses
#####################

.. code-block:: python

   req = Request(services.ECUReset, subfunction=1, data=b'\x77\x88\x99')
   my_connection.send(req.get_payload()) 
   payload = my_connection.wait_frame(timeout=1)
   response = Response.from_payload(payload)
   if response.service == service.ECUReset and response.code == Response.PositiveResponse and response.data == b'\x01':
      print('Success!')
   else:
      print('Reset failed')

Services
########

.. code-block:: python

   req = services.ECUReset.make_request(reset_type=1, data=b'\x77\x88\x99')
   my_connection.send(req.get_payload()) 
   payload = my_connection.wait_frame(timeout=1)
   response = Response.from_payload(payload)
   services.ECUReset.interpret_response(response)
   if response.service == service.ECUReset and response.code == Response.PositiveResponse and response.service_data.reset_type_echo == 1:
      print('Success!')
   else:
      print('Reset failed')

Client
######

.. code-block:: python

   try:
      client.ecu_reset(reset_type=1, data=b'\x77\x88\x99')
      print('Success!')
   except:
      print('Reset failed')

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

   def myalgo(seed, params):
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
   from udsoncan.Connection import IsoTPConnection
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

   conn = IsoTPConnection('vcan0', rxid=0x123, txid=0x456)
   with Client(conn,  request_timeout=2, config=config) as client:
      vin = client.read_data_by_identifier(0xF190)     
      print(vin)  # 'ABCDE0123456789' (15 chars)



.. _iocontrol_composite_did:

InputOutputControlByIdentifier Composite DID
--------------------------------------------

This example shows how the InputOutputControlByIdentifier can be used with a composite data identifier and how to build a proper `ioconfig` dict.

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