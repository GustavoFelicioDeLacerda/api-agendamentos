from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Agendamento, Fidelidade, Endereco


class AgendamentoSerializer(serializers.ModelSerializer):
    prestador = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True
    )

    class Meta:
        model = Agendamento
        fields = [
            "id",
            "prestador",
            "nome_cliente",
            "email_cliente",
            "telefone_cliente",
            "data_horario",
            "estado",
            "criado_em",
        ]
        read_only_fields = ["id", "estado", "criado_em"]


class FidelidadeSerializer(serializers.ModelSerializer):
    cliente = serializers.SlugRelatedField(slug_field="username", read_only=True)
    prestador = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Fidelidade
        fields = ["id", "cliente", "prestador", "pontos"]


class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = ["id", "cep", "estado", "cidade", "bairro", "rua", "complemento"]