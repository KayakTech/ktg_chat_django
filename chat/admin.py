from django.contrib import admin


from chat.models import ChatRoom


@admin.register(ChatRoom)
class ChatAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['name', 'room_id', 'created_at', 'updated_at',
                    'object_id', 'created_by']

    filter_horizontal = ['participants',]
