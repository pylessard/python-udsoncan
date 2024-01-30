Client
======
.. toctree::
    :maxdepth: 3 

.. _Client:

The UDS client is a simple client that works synchronously and can handle a single request/response at a time. When requesting a service, the client executes these tasks:

 - Builds a payload
 - Calls the connection `empty_rxqueue` method.
 - Sends the request
 - Waits for a response, with timeout
 - Interprets the response data
 - Validates the response content
 - Returns the response

The goal of this client is to simplify the usage of the **Services** object by exposing only useful arguments, hiding repetitive values, handling exceptions and logging. It can detect usage errors as well as malformed server responses. 

The client will raise a :ref:`NegativeResponseException<NegativeResponseException>` when the server responds with a negative response. 

The client may raise :ref:`InvalidResponseException<InvalidResponseException>` if the payload is incomplete or if the underlying service raises this exception while parsing the response data.

The client may raise :ref:`UnexpectedResponseException<UnexpectedResponseException>` if the response from the server does not match the last request sent. For example, if the service number in the response is different from the service number in the request. Another case would be if the echo of a parameter for a specific service does not match the request. For instance, if an ECUReset subfunction is the reset type, a valid server response will include an echo of the reset type in its payload.


.. autoclass:: udsoncan.client.Client

.. _client_config:

---------------

Configuration
-------------

The client configuration must be a dictionary with the following keys defined:

.. _config_exception_on_negative_response:

.. attribute:: exception_on_negative_response
   :annotation: (bool)

   When set to `True`, the client will raise a :ref:`NegativeResponseException<NegativeResponseException>` when the server responds with a negative response.
   When set to `False`, the returned `Response` will have its property `positive` set to False

.. _config_exception_on_invalid_response:

.. attribute:: exception_on_invalid_response
   :annotation: (bool)

   When set to `True`, the client will raise a :ref:`InvalidResponseException<InvalidResponseException>` when the underlying service `interpret_response` raises the same exception.
   When set to `False`, the returned `Response` will have its property `valid` set to False 

.. _config_exception_on_unexpected_response:

.. attribute:: exception_on_unexpected_response
   :annotation: (bool)

   When set to ``True``, the client will raise a :ref:`UnexpectedResponseException<UnexpectedResponseException>` when the server returns a response that is not expected. For instance, a response for a different service or when the subfunction echo doesn't match the request.
   When set to ``False``, the returned `Response` will have its property ``unexpected`` set to True in the same case.

.. _config_security_algo:

.. attribute:: security_algo
   :annotation: (callable)

   The implementation of the security algorithm necessary for the :ref:`SecurityAccess<SecurityAccess>` service. This function must have the following signatures: 
      
      .. function:: SomeAlgorithm(level, seed, params)

         :param level: The requested security level.
         :type level: int
         :param seed: The seed given by the server
         :type seed: bytes
         :param params: The value provided by the client configuration ``security_algo_params``
         :return: The security key
         :rtype: bytes

.. warning:: Starting from v1.12, parameters are passed by name, so their order is not important, but their name is. 
   Also, for backward compatibility, Python reflection is used to pass only arguments present in the signature. So a signature such as ``SomeAlgorithm()`` would be accepted.


See :ref:`an example <example_security_algo>`

.. _config_security_algo_params:

.. attribute:: security_algo_params
   :annotation: (...)

   This value will be given to the security algorithm defined in ``config['security_algo']``. This value can be any Python object, including a dictionary.

.. _config_data_identifiers:

.. attribute:: data_identifiers
   :annotation: (dict)

   This configuration is a dictionary that is mapping an integer (the data identifier) with a :ref:`DidCodec<DidCodec>`. These codecs will be used to convert values to byte payload and vice-versa when sending/receiving data for a service that needs a DID, i.e.:
   
      - :ref:`ReadDataByIdentifier<ReadDataByIdentifier>`
      - :ref:`WriteDataByIdentifier<WriteDataByIdentifier>`
      - :ref:`ReadDTCInformation<ReadDTCInformation>` with subfunction ``reportDTCSnapshotRecordByDTCNumber`` and ``reportDTCSnapshotRecordByRecordNumber``

   Possible configuration values are

      - ``string`` : The string will be used as a pack/unpack string when processing the data
      - ``DidCodec`` (class or instance) : The encode/decode method will be used to process the data

    The special dictionnary key `'default'` can be used to specify a fallback codec if an operation is done on a codec not part of the configuration. Useful for scanning a range of DID

.. _config_input_output:

.. attribute:: input_output
   :annotation: (dict)

   This configuration is a dictionary that is mapping an integer (the IO data identifier) with a :ref:`DidCodec<DidCodec>` specifically for the :ref:`InputOutputControlByIdentifier<InputOutputControlByIdentifier>` service. Just like config[data_identifers], these codecs will be used to convert values to byte payload and vice-versa when sending/receiving data.

   Since :ref:`InputOutputControlByIdentifier<InputOutputControlByIdentifier>` supports composite codecs, it is possible to provide a sub-dictionary as a codec specifying the bitmasks.

   Possible configuration values are:

      - ``string`` : The string will be used as a pack/unpack string when processing the data
      - ``DidCodec`` (class or instance) : The encode/decode method will be used to process the data
      - ``dict`` : The dictionary entry indicates a composite DID. Three subkeys must be defined as:

         - ``codec`` : The codec, a string or a DidCodec class/instance
         - ``mask`` : A dictionary mapping the mask name with a bit
         - ``mask_size`` : An integer indicating on how many bytes must the mask be encoded

    The special dictionnary key `'default'` can be used to specify a fallback codec if an operation is done on a codec not part of the configuration. Useful for scanning a range of DID
    
   See :ref:`this example<iocontrol_composite_did>` to see how IO codecs are defined.

.. _config_tolerate_zero_padding:

.. attribute:: tolerate_zero_padding
   :annotation: (bool)
   
   This value will be passed to the services 'interpret_response' when the parameter is supported as in :ref:`ReadDataByIdentifier<ReadDataByIdentifier>`, :ref:`ReadDTCInformation<ReadDTCInformation>`. It has to ignore trailing zeros in the response data to avoid falsely raising :ref:`InvalidResponseException<InvalidResponseException>` if the underlying protocol uses some zero-padding. 

.. _config_ignore_all_zero_dtc:

.. attribute:: ignore_all_zero_dtc
   :annotation: (bool)
   
   This value is used with the :ref:`ReadDTCInformation<ReadDTCInformation>` service when reading DTCs. It will skip any DTC that has an ID of 0x000000. If the underlying protocol uses zero-padding, it may generate a valid response data of all zeros. This parameter is different from ``config['tolerate_zero_padding']``. 

   Consider a server response that contains a list of DTCs where all DTCs must be 4 bytes long (ID and status). Say that the server returns a single DTC of value 0x123456, with status 0x78 over a transport protocol that uses zero-padding. Let's study 5 different payloads.

    1. ``1234567800``           (invalid)
    2. ``123456780000``         (invalid)
    3. ``12345678000000``       (invalid)
    4. ``1234567800000000``     (valid)
    5. ``123456780000000000``   (invalid)

   In this situation, all cases except case 4 would raise a :ref:`InvalidResponseException<InvalidResponseException>` because of their incorrect lengths (unless ``config['tolerate_zero_padding']`` is set to True). Case 4 would return 2 DTCs, the second DTC with an ID of 0x000000 and a status of 0x00. Setting ``config['ignore_all_zero_dtc']`` to True will make the functions return only the first valid DTC.

.. _config_server_address_format:

.. attribute:: server_address_format
   :annotation: (int)

   The :ref:`MemoryLocation<MemoryLocation>` server_address_format is the value to use when none is specified explicitly for methods expecting a parameter of type :ref:`MemoryLocation<MemoryLocation>`.

   See :ref:`an example<example_default_memloc_format>`

.. _config_server_memorysize_format:

.. attribute:: server_memorysize_format
   :annotation: (int)

   The :ref:`MemoryLocation<MemoryLocation>` server_memorysize_format is the value to use when none is specified explicitly for methods expecting a parameter of type :ref:`MemoryLocation<MemoryLocation>` 

   See :ref:`an example<example_default_memloc_format>`

.. _config_extended_data_size:

.. attribute:: extended_data_size
   :annotation: (dict[int] = int)
   
   This is the description of all the DTC extended data record sizes. This value is used to decode the server response when requesting a DTC extended data.
   The value must be specified as follows:

.. code-block:: python

   config['extended_data_size'] = {
      0x123456 : 45, # Extended data for DTC 0x123456 is 45 bytes long
      0x123457 : 23 # Extended data for DTC 0x123457 is 23 bytes long
   }

.. _config_dtc_snapshot_did_size:

.. attribute:: dtc_snapshot_did_size
   :annotation: (int)
   
   The number of bytes used to encode a data identifier specifically for :ref:`ReadDTCInformation<ReadDTCInformation>` subfunction ``reportDTCSnapshotRecordByDTCNumber`` and ``reportDTCSnapshotRecordByRecordNumber``. The UDS standard does not specify a DID size although all other services expect a DID encoded over 2 bytes (16 bits). Default value of 2

.. _config_standard_version:

.. attribute:: standard_version
   :annotation: (int)

   The standard version to use, valid values are : 2006, 2013, 2020.  
   Default value is 2020

.. _config_timeouts:
.. _config_request_timeout:

.. attribute:: request_timeout
   :annotation: (float)

   Maximum amount of time in seconds to wait for a response of any kind, positive or negative, after sending a request.
   After this time is elapsed, a TimeoutException will be raised regardless of other timeouts value or previous client responses.
   In particular even if the server requests that the client wait, by returning response requestCorrectlyReceived-ResponsePending (0x78),
   this timeout will still trigger.

   If you wish to disable this behaviour and have your server wait for as long as it takes for the ECU to finish whatever activity
   you have requested, set this value to None.

   Default value of 5

.. _config_p2_timeout:

.. attribute:: p2_timeout
   :annotation: (float)

   Maximum amount of time in seconds to wait for a first response (positive, negative, or NRC 0x78). After this time is elapsed, a TimeoutException will be raised if no response has been received.
   See ISO 14229-2:2013 (UDS Session Layer Services) for more details. 
   Default value of 1

.. _config_p2_star_timeout:

.. attribute:: p2_star_timeout
   :annotation: (float)

   Maximum amount of time in seconds to wait for a response (positive, negative, or NRC0x78) after the reception of a negative response with code 0x78
   (requestCorrectlyReceived-ResponsePending). After this time is elapsed, a TimeoutException will be raised if no response has been received. 
   See ISO 14229-2:2013 (UDS Session Layer Services) for more details.
   Default value of 5

.. _config_use_server_timing:

.. attribute:: use_server_timing
   :annotation: (bool)

   When using 2013 standard or above, the server is required to provide its P2 and P2* timing values with a DiagnosticSessionControl request. By setting this parameter to ``True``, the value received from the server will be used. When ``False``, these timing values will be ignored and local configuration timing will be used.  Note that no timeout value can exceed the ``config['request_timeout']`` as it is meant to avoid the client from hanging for too long.

   This parameter has no effect when ``config['standard_version']`` is set to ``2006``.

   Default value is True

-------------

Suppress positive response
--------------------------

The UDS standard proposes a mechanism to avoid treating useless positive responses. For all services using a subfunction byte, the client can set bit 7 of the subfunction byte to signal that no response is necessary if the response is positive. 
This bit is called the ``suppressPosRspMsgIndicationBit``

The ``Client`` object lets you use that feature by using ``suppress_positive_response`` into a ``with`` statement. See the following example:

.. code-block:: python

    with client.suppress_positive_response(wait_nrc=False):
        client.tester_present()   # Will not wait for a response and always return None
    
    with client.suppress_positive_response(wait_nrc=True):
        client.tester_present()   # Will wait in case an NRC is returned. 

When ``suppress_positive_response`` is askied for a service using a subfunction byte, the client will set suppressPosRspMsgIndicationBit before sending the request. 
If `wait_nrc` is `False` (default value), the client will not wait for any response and will disregard positive and negative responses if they happen. 
The response returned by the client function will always be ``None`` in that case.

If `wait_nrc` is `True`, the client will wait to see if a negative response is returned. In that scenario
 - No timeout will be raised if no response is received
 - If a positive response is received, it will not be validated and `None` will be returned
 - If a negative response is received, the normal processing will happen. Meaning either the response will be returned or a `NegativeResponseException` 
    will be raised, depending on :ref:`exception_on_negative_response<config_exception_on_negative_response>` parameter.

If ``suppress_positive_response`` is askied for a service with no subfunction byte, the directive will be ignored and a warning message will be logged.

-----

Overriding the output
---------------------

For mean of testing, it may be useful to send invalid payloads to the server and still want the ``Client`` object to parse the response of the server. 

It is possible to do so by using the ``payload_override`` property into a ``with`` statement. See the following example:

.. code-block:: python

   with client.payload_override(b'\x11\x22\x33'): # Client will send 112233 (hex) in every call within this "with" statement
      client.tester_present()

It is also possible to override with a function that modify the original output

.. code-block:: python
   
   def my_func(payload):
      return payload + b'\x00'  # Add extra 00 to the payload

   with client.payload_override(my_func): # Client will append 00 to its output
      client.tester_present()

When using that feature, the client will process the response from the server just like if a valid request was sent. The response may be :ref:`Invalid<InvalidResponseException>`, :ref:`Unexpected<UnexpectedResponseException>` or :ref:`Negative<NegativeResponseException>`.


.. note:: It is possible to change the behaviour of the client on failing requests. See the client parameters :ref:`exception_on_invalid_response<config_exception_on_invalid_response>`, :ref:`exception_on_unexpected_response<config_exception_on_unexpected_response>` and :ref:`exception_on_negative_response<config_exception_on_negative_response>`

-----

Methods by services
-------------------


:ref:`AccessTimingParameter<AccessTimingParameter>`
###################################################

.. automethod:: udsoncan.client.Client.read_extended_timing_parameters
.. automethod:: udsoncan.client.Client.reset_default_timing_parameters
.. automethod:: udsoncan.client.Client.read_active_timing_parameters
.. automethod:: udsoncan.client.Client.set_timing_parameters

-------------

:ref:`ClearDiagnosticInformation<ClearDiagnosticInformation>`
#############################################################

.. automethod:: udsoncan.client.Client.clear_dtc

-------------

:ref:`CommunicationControl<CommunicationControl>`
#################################################

.. automethod:: udsoncan.client.Client.communication_control

-------------

:ref:`ControlDTCSetting<ControlDTCSetting>`
###########################################

.. automethod:: udsoncan.client.Client.control_dtc_setting

-------------


:ref:`DiagnosticSessionControl<DiagnosticSessionControl>`
#########################################################

.. automethod:: udsoncan.client.Client.change_session

-------------

:ref:`DynamicallyDefineDataIdentifier<DynamicallyDefineDataIdentifier>`
#######################################################################

.. automethod:: udsoncan.client.Client.dynamically_define_did
.. note:: See :ref:`an example<example_define_dynamic_did>` showing how to define a dynamic DID.
.. automethod:: udsoncan.client.Client.clear_dynamically_defined_did
.. automethod:: udsoncan.client.Client.clear_all_dynamically_defined_did


-------------

:ref:`ECUReset<ECUReset>`
#########################

.. automethod:: udsoncan.client.Client.ecu_reset

-------------

:ref:`InputOutputControlByIdentifier<InputOutputControlByIdentifier>`
#####################################################################

.. automethod:: udsoncan.client.Client.io_control

-------------

:ref:`LinkControl<LinkControl>`
###############################

.. automethod:: udsoncan.client.Client.link_control

-------------

:ref:`ReadDataByIdentifier<ReadDataByIdentifier>`
#################################################

.. automethod:: udsoncan.client.Client.read_data_by_identifier
.. automethod:: udsoncan.client.Client.read_data_by_identifier_first
.. automethod:: udsoncan.client.Client.test_data_identifier

-------------

:ref:`ReadDTCInformation<ReadDTCInformation>`
#############################################


.. automethod:: udsoncan.client.Client.get_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_user_defined_memory_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_emission_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_mirrormemory_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_dtc_by_status_severity_mask
.. automethod:: udsoncan.client.Client.get_number_of_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_mirrormemory_number_of_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_number_of_emission_dtc_by_status_mask
.. automethod:: udsoncan.client.Client.get_number_of_dtc_by_status_severity_mask
.. automethod:: udsoncan.client.Client.get_dtc_severity
.. automethod:: udsoncan.client.Client.get_supported_dtc
.. automethod:: udsoncan.client.Client.get_first_test_failed_dtc
.. automethod:: udsoncan.client.Client.get_first_confirmed_dtc
.. automethod:: udsoncan.client.Client.get_most_recent_test_failed_dtc
.. automethod:: udsoncan.client.Client.get_most_recent_confirmed_dtc
.. automethod:: udsoncan.client.Client.get_dtc_with_permanent_status
.. automethod:: udsoncan.client.Client.get_dtc_fault_counter
.. automethod:: udsoncan.client.Client.get_dtc_snapshot_identification
.. automethod:: udsoncan.client.Client.get_dtc_snapshot_by_dtc_number
.. automethod:: udsoncan.client.Client.get_user_defined_dtc_snapshot_by_dtc_number
.. automethod:: udsoncan.client.Client.get_dtc_snapshot_by_record_number
.. automethod:: udsoncan.client.Client.get_dtc_extended_data_by_dtc_number
.. automethod:: udsoncan.client.Client.get_dtc_extended_data_by_record_number
.. automethod:: udsoncan.client.Client.get_user_defined_dtc_extended_data_by_dtc_number
.. automethod:: udsoncan.client.Client.get_mirrormemory_dtc_extended_data_by_dtc_number


-------------

:ref:`ReadMemoryByAddress<ReadMemoryByAddress>`
###############################################

.. automethod:: udsoncan.client.Client.read_memory_by_address
.. note:: See :ref:`an example<example_default_memloc_format>` showing how to use default format configuration.

-------------

:ref:`RequestDownload<RequestDownload>`
#######################################

.. automethod:: udsoncan.client.Client.request_download
.. note:: See :ref:`an example<example_default_memloc_format>` showing how to use default format configuration.

-------------

:ref:`RequestTransferExit<RequestTransferExit>`
###############################################

.. automethod:: udsoncan.client.Client.request_transfer_exit

-------------

:ref:`RequestUpload<RequestUpload>`
###################################

.. automethod:: udsoncan.client.Client.request_upload
.. note:: See :ref:`an example<example_default_memloc_format>` showing how to use default format configuration.

-------------

:ref:`RoutineControl<RoutineControl>`
#####################################

.. automethod:: udsoncan.client.Client.start_routine
.. automethod:: udsoncan.client.Client.stop_routine
.. automethod:: udsoncan.client.Client.get_routine_result

-------------

:ref:`SecurityAccess<SecurityAccess>`
#####################################

.. automethod:: udsoncan.client.Client.request_seed
.. automethod:: udsoncan.client.Client.send_key
.. automethod:: udsoncan.client.Client.unlock_security_access

.. note:: See :ref:`this example<example_security_algo>` to see how to define the security algorithm

-------------

:ref:`TesterPresent<TesterPresent>`
###################################

.. automethod:: udsoncan.client.Client.tester_present

-------------

:ref:`TransferData<TransferData>`
#################################

.. automethod:: udsoncan.client.Client.transfer_data

-------------

:ref:`WriteDataByIdentifier<WriteDataByIdentifier>`
###################################################

.. automethod:: udsoncan.client.Client.write_data_by_identifier

.. note:: If the DID Codec that is written is defined with a pack string (default codec), multiple values may be passed with a tuple.

-------------

:ref:`WriteMemoryByAddress<WriteMemoryByAddress>`
#################################################

.. automethod:: udsoncan.client.Client.write_memory_by_address

-------------

:ref:`RequestFileTransfer<RequestFileTransfer>`
###############################################

.. automethod:: udsoncan.client.Client.add_file
.. automethod:: udsoncan.client.Client.delete_file
.. automethod:: udsoncan.client.Client.replace_file
.. automethod:: udsoncan.client.Client.read_file
.. automethod:: udsoncan.client.Client.read_dir
.. automethod:: udsoncan.client.Client.resume_file

-------------

:ref:`Authentication<Authentication>`
#############################################

.. automethod:: udsoncan.client.Client.authentication
.. automethod:: udsoncan.client.Client.deauthenticate
.. automethod:: udsoncan.client.Client.verify_certificate_unidirectional
.. automethod:: udsoncan.client.Client.verify_certificate_bidirectional
.. automethod:: udsoncan.client.Client.proof_of_ownership
.. automethod:: udsoncan.client.Client.transmit_certificate
.. automethod:: udsoncan.client.Client.request_challenge_for_authentication
.. automethod:: udsoncan.client.Client.verify_proof_of_ownership_unidirectional
.. automethod:: udsoncan.client.Client.verify_proof_of_ownership_bidirectional
.. automethod:: udsoncan.client.Client.authentication_configuration
