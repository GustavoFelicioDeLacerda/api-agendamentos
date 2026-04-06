from django.db import models
from django.contrib.auth.models import User


class Agendamento(models.Model):

    class Estado(models.TextChoices):
        NAO_CONFIRMADO = "NAO_CONFIRMADO", "Não confirmado"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"
        EXECUTADO = "EXECUTADO", "Executado"

    prestador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agendamentos"
    )
    nome_cliente = models.CharField(max_length=200)
    email_cliente = models.EmailField()
    telefone_cliente = models.CharField(max_length=20)
    data_horario = models.DateTimeField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NAO_CONFIRMADO
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_cliente} - {self.data_horario} [{self.estado}]"


class Fidelidade(models.Model):
    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fidelidades_cliente"
    )
    prestador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fidelidades_prestador"
    )
    pontos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("cliente", "prestador")

    def __str__(self):
        return f"{self.cliente.username} -> {self.prestador.username}: {self.pontos} pontos"


class Endereco(models.Model):
    prestador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="endereco"
    )
    cep = models.CharField(max_length=8)
    estado = models.CharField(max_length=2)
    cidade = models.CharField(max_length=100)
    bairro = models.CharField(max_length=100)
    rua = models.CharField(max_length=200)
    complemento = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"{self.rua}, {self.cidade} - {self.estado}"