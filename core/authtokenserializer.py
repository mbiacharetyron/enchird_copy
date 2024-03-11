from django.contrib.auth import authenticate
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework import serializers


class CustomAuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        label=_("Username"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        username = attrs.get('username')
        print(username)
        password = attrs.get('password')
        print(password)

        if username and password:
            print("1")
            user = authenticate(request=self.context.get('request'),
                                username=username, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            print("1")
            
            if not user:
                print("2")

                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

    def to_representation(self, instance):
        # Customize the error response format
        if 'non_field_errors' in instance:
            return {'error': instance['non_field_errors'][0]}
        return super().to_representation(instance)

