import socket

class RPCService:
  
  def __init__(self,host,port):
    self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.client.connect((host, port))

  def send_message(self, message):
     self.client.sendall(message.encode())
     #response = client_socket.recv(1024).decode()
     #print(f'Received response: {response}')
    
  def close(self):
      self.client.close()
