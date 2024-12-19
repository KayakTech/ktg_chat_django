from chat import views

from rest_framework.routers import DefaultRouter

app_name = 'chat'
router = DefaultRouter()
router.register("rooms", views.RoomView, basename="rooms")

router.register("chats", views.ChatView, basename="chat")

router.register("participants", views.ParticipantView, basename="participants")

router.register("attachments", views.AttachmentView, basename="attachments")


urlpatterns = [

]


urlpatterns += router.urls
