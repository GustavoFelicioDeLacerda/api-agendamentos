from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date
import requests
from django.conf import settings

from .models import Agendamento, Fidelidade, Endereco
from .serializers import AgendamentoSerializer, FidelidadeSerializer, EnderecoSerializer
from .permissions import IsPrestador
from .utils import get_horarios_disponiveis, is_feriado


class AgendamentoListCreateView(generics.ListCreateAPIView):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        username = self.request.query_params.get("username")
        estado = self.request.query_params.get("estado")

        qs = Agendamento.objects.all()

        if username:
            qs = qs.filter(prestador__username=username)

        if estado:
            qs = qs.filter(estado=estado.upper())

        return qs

    def perform_create(self, serializer):
        prestador_username = self.request.data.get("prestador")

        try:
            prestador = User.objects.get(username=prestador_username)
        except User.DoesNotExist:
            raise ValidationError({"erro": "Prestador não encontrado."})

        data_horario = serializer.validated_data.get("data_horario")

        if is_feriado(data_horario.date()):
            raise ValidationError(
                {"erro": "Não é possível agendar em feriados nacionais."}
            )

        serializer.save(prestador=prestador)


class AgendamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated, IsPrestador]

    def perform_destroy(self, instance):
        instance.estado = Agendamento.Estado.CANCELADO
        instance.save()


class AgendamentoConfirmarView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPrestador]

    def post(self, request, pk):
        try:
            agendamento = Agendamento.objects.get(pk=pk)
        except Agendamento.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, agendamento)

        if agendamento.estado != Agendamento.Estado.NAO_CONFIRMADO:
            return Response(
                {"erro": "Apenas agendamentos não confirmados podem ser confirmados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        agendamento.estado = Agendamento.Estado.CONFIRMADO
        agendamento.save()

        try:
            cliente_user = User.objects.get(email=agendamento.email_cliente)

            fidelidade, _ = Fidelidade.objects.get_or_create(
                cliente=cliente_user,
                prestador=agendamento.prestador
            )

            fidelidade.pontos += 1
            fidelidade.save()

        except User.DoesNotExist:
            pass

        serializer = AgendamentoSerializer(agendamento)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgendamentoExecutarView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPrestador]

    def post(self, request, pk):

        try:
            agendamento = Agendamento.objects.get(pk=pk)
        except Agendamento.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, agendamento)

        if agendamento.estado != Agendamento.Estado.CONFIRMADO:
            return Response(
                {"erro": "Apenas agendamentos confirmados podem ser executados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        agendamento.estado = Agendamento.Estado.EXECUTADO
        agendamento.save()

        serializer = AgendamentoSerializer(agendamento)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HorariosDisponiveisView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):

        username = request.query_params.get("username")
        data_str = request.query_params.get("data")

        if not username or not data_str:
            return Response(
                {"erro": "Parâmetros 'username' e 'data' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            prestador = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"erro": "Prestador não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            data = date.fromisoformat(data_str)
        except ValueError:
            return Response(
                {"erro": "Data inválida. Use o formato YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        horarios = get_horarios_disponiveis(data, prestador)

        return Response({
            "horarios_disponiveis": horarios
        })


class EnderecoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):

        try:
            prestador = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"erro": "Prestador não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        cep = request.data.get("cep")

        if not cep:
            return Response(
                {"erro": "CEP é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        dados = {
            "cep": cep,
            "estado": request.data.get("estado"),
            "cidade": request.data.get("cidade"),
            "bairro": request.data.get("bairro"),
            "rua": request.data.get("rua"),
            "complemento": request.data.get("complemento", ""),
        }

        if not all([dados["estado"], dados["cidade"], dados["bairro"], dados["rua"]]):

            url = f"{settings.BRASILAPI_URL}/api/cep/v1/{cep}"

            resp = requests.get(url)

            if resp.status_code != 200:
                return Response(
                    {"erro": "CEP inválido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cep_data = resp.json()

            dados.update({
                "estado": cep_data.get("state", ""),
                "cidade": cep_data.get("city", ""),
                "bairro": cep_data.get("neighborhood", ""),
                "rua": cep_data.get("street", ""),
            })

        serializer = EnderecoSerializer(data=dados)

        if serializer.is_valid():
            serializer.save(prestador=prestador)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)