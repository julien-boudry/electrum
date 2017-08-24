import sys
sys.path.insert(0, "lib/ln")
from .ln import rpc_pb2_grpc, rpc_pb2
import os
from . import keystore, bitcoin, network, daemon, interface
import socket

import grpc
import concurrent.futures as futures
import time

bitcoin.set_simnet()

WALLET = None
NETWORK = None

rand = bytes([
		0xb7, 0x94, 0x38, 0x5f, 0x2d, 0x1e, 0xf7, 0xab,
		0x4d, 0x92, 0x73, 0xd1, 0x90, 0x63, 0x81, 0xb4,
		0x4f, 0x2f, 0x6f, 0x25, 0x18, 0xa3, 0xef, 0xb9,
		0x64, 0x49, 0x18, 0x83, 0x31, 0x98, 0x47, 0x53
])
#k = keystore.BIP32_KeyStore({})
#k.add_xprv_from_seed(rand, 0, 'm/0/0')
#assert k.xpub is not None
#pubkey = bytearray.fromhex(k.derive_pubkey(False, 0))
#print(pubkey)
K, K_compressed = bitcoin.get_pubkeys_from_secret(rand)
pubk = bitcoin.public_key_to_p2pkh(K_compressed) # really compressed?
print(pubk)
assert len(pubk) <= 35
print(bitcoin.public_key_to_p2wpkh(K_compressed))

class LightningImpl(rpc_pb2_grpc.ElectrumBridgeServicer):
  def ConfirmedBalance(self, request, context):
    m = rpc_pb2.ConfirmedBalanceResponse()
    confs = request.confirmations
    witness = request.witness # bool
    m.amount = sum(q(pubk).values()) + sum(q(bitcoin.public_key_to_p2wpkh(K_compressed)).values())
    return m
  def NewAddress(self, request, context):
    m = rpc_pb2.NewAddressResponse()
    if request.type == rpc_pb2.NewAddressRequest.WITNESS_PUBKEY_HASH:
      m.address = bitcoin.public_key_to_p2wpkh(K_compressed)
      #m.address = bitcoin.base_encode(b"\x19\x00\x00" + bitcoin.hash_160(K) + bitcoin.Hash(b"\x19\x00\x00" + bitcoin.hash_160(K))[:4], 58)
    elif request.type == rpc_pb2.NewAddressRequest.NESTED_PUBKEY_HASH:
      assert False
    elif request.type == rpc_pb2.NewAddressRequest.PUBKEY_HASH:
      m.address = bitcoin.public_key_to_p2pkh(K_compressed)
    else:
      assert False
    return m
  def FetchRootKey(self, request, context):
    m = rpc_pb2.FetchRootKeyResponse()
    m.rootKey = K_compressed
    return m

def q(pubk):
  #print(NETWORK.synchronous_get(('blockchain.address.get_balance', [pubk]), timeout=1))
  # create an INET, STREAMing socket
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # now connect to the web server on port 80 - the normal http port
  s.connect(("localhost", 50001))
  i = interface.Interface("localhost:50001:garbage", s)
  i.queue_request('blockchain.address.get_balance', [pubk], 42) # 42 is id
  i.send_requests()
  time.sleep(.1)
  res = i.get_responses()
  assert len(res) == 1
  print(res[0][1])
  return res[0][1]["result"]

def serve(config):
  print(q(pubk))

  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  rpc_pb2_grpc.add_ElectrumBridgeServicer_to_server(
      LightningImpl(), server)
  server.add_insecure_port('[::]:9090')
  server.start()
  try:
    while True:
      time.sleep(10)
  except KeyboardInterrupt:
    server.stop(0)

def test_lightning(wallet, networ, config):
  global WALLET, NETWORK
  WALLET = wallet
  #assert networ is not None
  NETWORK = networ
  serve(config)

if __name__ == '__main__':
  serve()
