import json
import logging
from knox.models import AuthToken
from knox.settings import CONSTANTS
from apis.users.models import User
from apis.messaging.models import *
from asgiref.sync import async_to_sync
from knox.auth import TokenAuthentication
from channels.consumer import SyncConsumer
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer


logger = logging.getLogger("myLogger")




class GroupChatConsumer(SyncConsumer):
    
    def websocket_connect(self, event): 
        try:
            usr = self.scope['url_route']['kwargs']['user_id']
            group_id = self.scope['url_route']['kwargs']['group_id']
            
            # user = self.get_user(usr)
            # print(user)
            self.group_name = f"group_{group_id}"
            print(self.group_name)
            
            try:
                user = User.objects.get(id=usr, is_deleted=False)
                group = ChatGroup.objects.get(id=group_id)
            except User.DoesNotExist:
                print(f"User with id={usr} not found or is deleted.")
                # async_to_sync(self.close)()
                raise DenyConnection("User not found or is deleted")
            except ChatGroup.DoesNotExist:
                print(f"ChatGroup with id={group_id} not found or is deleted.")
                raise DenyConnection("User not found or is deleted")

            self.send({
                'type': 'websocket.accept'
            }) 
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            print(f'[{self.channel_name}] - You are connected')
            
        except Exception as e:
            print("An error occured:", str(e))
            
    
    def websocket_disconnect(self, event):
        print(f'[{self.channel_name}] - You are Disconnected')
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        print(event)
        
        
    # Received from the frontend to be send using the websocket_message function
    def websocket_receive(self, text_data):
        try:
            print(f'[{self.channel_name}] - Received Message - {text_data["text"]}')
            
            # Parse the incoming JSON message
            text_data_json = json.loads(text_data["text"])
            message = text_data_json
            print(text_data_json.get("message"))
            
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "websocket.message",
                    "text": message,
                }
            )
        except Exception as e:
            print("An error occured:", str(e))


    def websocket_message(self, event):
        try:
            print(f'[{self.channel_name}] - Received Sent - {event["text"]}')
            data = event['text']
            
            try:
                get_group_by_name = ChatGroup.objects.get(id=data['group_id'])
                print(get_group_by_name)
                
                try:
                    user = User.objects.get(id=data['sender'], is_deleted=False)
                except User.DoesNotExist:
                    print(f"User with id={data['sender']} not found or is deleted.")
                    # async_to_sync(self.close)()
                    raise DenyConnection("User not found or is deleted")
                
                
                new_message = GroupMessage(group=get_group_by_name, sender=user, content=data['message'])
                new_message.save()
                
                response_data = {
                    'sender': data['sender'],
                    'message': data['message']
                }
                
                self.send({ 
                    "type": "websocket.send",
                    'text': json.dumps(response_data),
                })
            except Exception as e:
                print("An error occurred while processing and sending the message:", str(e))

        except Exception as e:
            print("An error occured:", str(e))
    


class ChatConsumer(SyncConsumer):
    
    def websocket_connect(self, event): 
        try:
            other_usr = self.scope['url_route']['kwargs']['other_user']
            user = self.scope["user"]
            
            try:
                other_user = User.objects.get(id=other_usr, is_deleted=False)
            except ChatGroup.DoesNotExist:
                logger.error(f"User with id={other_usr} not found or is deleted.", extra={'user': "Anonymous"})
                print(f"User with id={other_usr} not found or is deleted.")
                raise DenyConnection(f"User with id={other_usr} not found or is deleted.")
            print(other_user)
            # Check if the user is admin or tutor
            if not user.is_a_teacher and not user.is_admin:
                logger.error("User is not authorized to connect.", extra={'user': user.id})
                raise DenyConnection("User is not authorized to connect")

            # Check if other_user is admin or tutor
            if not other_user.is_a_teacher and not other_user.is_admin:
                logger.error("User you are trying to message is not authorized to connect", extra={'user': user.id})
                raise DenyConnection("User you are trying to message is not authorized to connect")
            
            # Check if user is trying to message themselves.
            if user.id == other_user.id:
                logger.error("You cannot send message to yourself", extra={'user': user.id})
                raise DenyConnection("You cannot send message to yourself")
            
            self.group_name = self.get_or_create_chat(user.id, other_user.id)
            print(self.group_name)

            self.send({
                'type': 'websocket.accept'
            }) 
            async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            print(f'[{self.channel_name}] - You are connected')
            
        except Exception as e:
            logger.error("An error occured while trying to connect:", extra={'user': user.id})
            print("An error occured while trying to connect:", str(e))
            
    
    def websocket_disconnect(self, event):
        print(f'[{self.channel_name}] - You are Disconnected')
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        print(event)
        
    # Received from the frontend to be send using the websocket_message function
    def websocket_receive(self, text_data):
        try:
            print(f'[{self.channel_name}] - Received Message - {text_data["text"]}')
            print(str(self.scope["user"].id))
            
            # Parse the incoming JSON message
            text_data_json = json.loads(text_data["text"])
            message = text_data_json
            print(text_data_json)
            print(text_data_json.get("message"))
            
            # Check if the sender matches the current user
            if message.get("sender") != str(self.scope["user"].id):
                return
            
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "websocket.message",
                    "text": message,
                }
            )
        except Exception as e:
            print("An error occured:", str(e))


    def websocket_message(self, event):
        try:
            print(event)
            print(f'[{self.channel_name}] - Sent Message - {event["text"]}')
            data = event['text']
            print(data)
            try:
                sender_user = User.objects.get(id=data['sender'])
                print(sender_user)
                receiver_user = User.objects.get(id=data['receiver'])
                print(receiver_user)
                
                # Check if the sender and receiver are valid users
                if sender_user == self.scope["user"]:
                    new_message = DirectMessage(sender=sender_user, receiver=receiver_user, content=data['message'])
                    new_message.save()
                
                    response_data = {
                        'sender': data['sender'],
                        'message': data['message']
                    }
                
                    self.send({ 
                        "type": "websocket.send",
                        'text': json.dumps(response_data),
                    })
                elif sender_user != self.scope["user"] and receiver_user == self.scope["user"]:
                    response_data = {
                        'sender': data['sender'],
                        'message': data['message']
                    }
                
                    self.send({ 
                        "type": "websocket.send",
                        'text': json.dumps(response_data),
                    })
                    
            except Exception as e:
                print("An error occurred while processing and sending the message:", str(e))

        except Exception as e:
            print("An error occured:", str(e))
    

    def get_or_create_chat(self, user_id, other_user_id):
            users = [user_id, other_user_id]
            users.sort()
            group_name = f"chat_{users[0]}_{users[1]}"
            return group_name



# class ChatConsumer(AsyncWebsocketConsumer):
#     # def websocket__
#     async def connect(self): 
#         # me = self.scope['user']
#         usr = self.scope['url_route']['kwargs']['user_id']
#         other_usr = self.scope['url_route']['kwargs']['other_user']
        
#         user = User.objects.get(id=usr, is_deleted=False)
#         other_user = User.objects.get(id=other_usr, is_deleted=False)
        
#         self.group_name = f"thread_{other_user.id}-{user}"
#         print(f'[{self.channel_name}] - You are connected')
        
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()
        
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json
#         print(message)

#         event = {
#             'type': 'send_message',
#             'message': message,
#         }

#         await self.channel_layer.group_send(self.group_name, event)

#     async def send_message(self, event):

#         data = event['message']
#         await self.create_message(data=data)

#         response_data = {
#             'sender': data['sender'],
#             'message': data['message']
#         }
#         await self.send(text_data=json.dumps({'message': response_data}))

#     @database_sync_to_async
#     def create_message(self, data):

#         get_room_by_name = ChatGroup.objects.get(name=data['group_name'])
        
#         if not DirectMessage.objects.filter(content=data['message']).exists():
#             new_message = DirectMessage(group=get_room_by_name, sender=data['sender'], content=data['message'])
#             new_message.save()  
 
 
        