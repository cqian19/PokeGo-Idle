# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Networking/Responses/GetInventoryResponse.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from Inventory import InventoryDelta_pb2 as Inventory_dot_InventoryDelta__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='Networking/Responses/GetInventoryResponse.proto',
  package='POGOProtos.Networking.Responses',
  syntax='proto3',
  serialized_pb=_b('\n/Networking/Responses/GetInventoryResponse.proto\x12\x1fPOGOProtos.Networking.Responses\x1a\x1eInventory/InventoryDelta.proto\"f\n\x14GetInventoryResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12=\n\x0finventory_delta\x18\x02 \x01(\x0b\x32$.POGOProtos.Inventory.InventoryDeltab\x06proto3')
  ,
  dependencies=[Inventory_dot_InventoryDelta__pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_GETINVENTORYRESPONSE = _descriptor.Descriptor(
  name='GetInventoryResponse',
  full_name='POGOProtos.Networking.Responses.GetInventoryResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='POGOProtos.Networking.Responses.GetInventoryResponse.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='inventory_delta', full_name='POGOProtos.Networking.Responses.GetInventoryResponse.inventory_delta', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=116,
  serialized_end=218,
)

_GETINVENTORYRESPONSE.fields_by_name['inventory_delta'].message_type = Inventory_dot_InventoryDelta__pb2._INVENTORYDELTA
DESCRIPTOR.message_types_by_name['GetInventoryResponse'] = _GETINVENTORYRESPONSE

GetInventoryResponse = _reflection.GeneratedProtocolMessageType('GetInventoryResponse', (_message.Message,), dict(
  DESCRIPTOR = _GETINVENTORYRESPONSE,
  __module__ = 'Networking.Responses.GetInventoryResponse_pb2'
  # @@protoc_insertion_point(class_scope:POGOProtos.Networking.Responses.GetInventoryResponse)
  ))
_sym_db.RegisterMessage(GetInventoryResponse)


# @@protoc_insertion_point(module_scope)