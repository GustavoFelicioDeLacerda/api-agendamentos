from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from datetime import datetime, timezone, timedelta, date
from unittest import mock
from .models import Agendamento, Fidelidade, Endereco


class AgendamentoAPITestCase(APITestCase):
    def setUp(self):
        self.prestador1 = User.objects.create_user(username="alice", password="123", email="alice@teste.com")
        self.prestador2 = User.objects.create_user(username="bob", password="123", email="bob@teste.com")

        tz_brasil = timezone(timedelta(hours=-3))

        self.agendamento1 = Agendamento.objects.create(
            data_horario=datetime(2024, 3, 22, 10, 0, tzinfo=tz_brasil),
            nome_cliente="Carl",
            email_cliente="carl@codar.me",
            telefone_cliente="+5521999978888",
            prestador=self.prestador1
        )
        self.agendamento2 = Agendamento.objects.create(
            data_horario=datetime(2024, 3, 22, 11, 0, tzinfo=tz_brasil),
            nome_cliente="Ana",
            email_cliente="ana@teste.com",
            telefone_cliente="+5521999912345",
            prestador=self.prestador2
        )

        self.url_list_create = "/api/agendamentos/"

    def test_listagem_agendamentos_prestador_autenticado(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.get(f"{self.url_list_create}?username=alice")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["nome_cliente"] == "Carl"

    def test_listagem_filtro_por_estado(self):
        self.client.force_authenticate(user=self.prestador1)
        self.agendamento1.estado = Agendamento.Estado.CONFIRMADO
        self.agendamento1.save()
        response = self.client.get(f"{self.url_list_create}?username=alice&estado=confirmado")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["estado"] == "CONFIRMADO"

    @mock.patch("agenda.utils.is_feriado", return_value=False)
    def test_criacao_agendamento_valido(self, mock_feriado):
        data = {
            "data_horario": "2024-03-23T14:00:00-03:00",
            "nome_cliente": "Gustavo",
            "email_cliente": "gustavo@teste.com",
            "telefone_cliente": "+552199998877",
            "prestador": "bob"
        }
        response = self.client.post(self.url_list_create, data)
        assert response.status_code == 201
        assert response.data["nome_cliente"] == "Gustavo"
        assert response.data["estado"] == "NAO_CONFIRMADO"

        agendamento_id = response.data["id"]
        self.client.force_authenticate(user=self.prestador2)
        get_response = self.client.get(f"/api/agendamentos/{agendamento_id}/")
        assert get_response.status_code == 200
        assert get_response.data["email_cliente"] == "gustavo@teste.com"

    @mock.patch("agenda.utils.is_feriado", return_value=True)
    def test_criacao_agendamento_em_feriado(self, mock_feriado):
        data = {
            "data_horario": "2024-01-01T10:00:00-03:00",
            "nome_cliente": "Gustavo",
            "email_cliente": "gustavo@teste.com",
            "telefone_cliente": "+552199998877",
            "prestador": "bob"
        }
        response = self.client.post(self.url_list_create, data)
        assert response.status_code == 400

    def test_criacao_agendamento_invalido(self):
        data = {"nome_cliente": "", "prestador": "alice"}
        response = self.client.post(self.url_list_create, data)
        assert response.status_code == 400

    def test_usuario_nao_acessa_agendamento_outro_prestador(self):
        self.client.force_authenticate(user=self.prestador2)
        response = self.client.get(f"/api/agendamentos/{self.agendamento1.id}/")
        assert response.status_code == 403

    def test_usuario_acessa_agendamento_proprio(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.get(f"/api/agendamentos/{self.agendamento1.id}/")
        assert response.status_code == 200
        assert response.data["nome_cliente"] == "Carl"

    def test_update_agendamento_prestador(self):
        self.client.force_authenticate(user=self.prestador1)
        data = {"nome_cliente": "Carlos Atualizado"}
        response = self.client.patch(f"/api/agendamentos/{self.agendamento1.id}/", data)
        assert response.status_code == 200
        assert response.data["nome_cliente"] == "Carlos Atualizado"

    def test_delete_agendamento_prestador(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.delete(f"/api/agendamentos/{self.agendamento1.id}/")
        assert response.status_code == 204
        self.agendamento1.refresh_from_db()
        assert self.agendamento1.estado == Agendamento.Estado.CANCELADO

    def test_confirmar_agendamento(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post(f"/api/agendamentos/{self.agendamento1.id}/confirmar/")
        assert response.status_code == 200
        self.agendamento1.refresh_from_db()
        assert self.agendamento1.estado == Agendamento.Estado.CONFIRMADO

    def test_confirmar_agendamento_ja_confirmado(self):
        self.agendamento1.estado = Agendamento.Estado.CONFIRMADO
        self.agendamento1.save()
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post(f"/api/agendamentos/{self.agendamento1.id}/confirmar/")
        assert response.status_code == 400

    def test_outro_prestador_nao_pode_confirmar(self):
        self.client.force_authenticate(user=self.prestador2)
        response = self.client.post(f"/api/agendamentos/{self.agendamento1.id}/confirmar/")
        assert response.status_code == 403

    def test_confirmar_agendamento_inexistente(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post("/api/agendamentos/9999/confirmar/")
        assert response.status_code == 404

    def test_executar_agendamento_confirmado(self):
        self.agendamento1.estado = Agendamento.Estado.CONFIRMADO
        self.agendamento1.save()
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post(f"/api/agendamentos/{self.agendamento1.id}/executar/")
        assert response.status_code == 200
        self.agendamento1.refresh_from_db()
        assert self.agendamento1.estado == Agendamento.Estado.EXECUTADO

    def test_executar_agendamento_nao_confirmado(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post(f"/api/agendamentos/{self.agendamento1.id}/executar/")
        assert response.status_code == 400

    def test_executar_agendamento_inexistente(self):
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.post("/api/agendamentos/9999/executar/")
        assert response.status_code == 404

    def test_fidelidade_ao_confirmar(self):
        cliente_user = User.objects.create_user(
            username="carl", password="123", email="carl@codar.me"
        )
        self.client.force_authenticate(user=self.prestador1)
        self.client.post(f"/api/agendamentos/{self.agendamento1.id}/confirmar/")
        fidelidade = Fidelidade.objects.get(cliente=cliente_user, prestador=self.prestador1)
        assert fidelidade.pontos == 1

    def test_sem_fidelidade_email_nao_cadastrado(self):
        self.client.force_authenticate(user=self.prestador1)
        self.client.post(f"/api/agendamentos/{self.agendamento1.id}/confirmar/")
        assert not Fidelidade.objects.filter(prestador=self.prestador1).exists()

    def test_agendamento_timezone(self):
        tz_brasil = timezone(timedelta(hours=-3))
        dt_brasil = datetime(2024, 3, 22, 10, 0, tzinfo=tz_brasil)
        assert self.agendamento1.data_horario == dt_brasil

    def test_str_agendamento(self):
        assert "Carl" in str(self.agendamento1)

    def test_str_fidelidade(self):
        cliente_user = User.objects.create_user(
            username="carl", password="123", email="carl@codar.me"
        )
        fidelidade = Fidelidade.objects.create(
            cliente=cliente_user,
            prestador=self.prestador1,
            pontos=5
        )
        assert "carl" in str(fidelidade)
        assert "alice" in str(fidelidade)

    def test_str_endereco(self):
        endereco = Endereco.objects.create(
            prestador=self.prestador1,
            cep="22220050",
            estado="RJ",
            cidade="Rio de Janeiro",
            bairro="Flamengo",
            rua="Rua dos Pinheiros"
        )
        assert "Rio de Janeiro" in str(endereco)


class HorariosDisponiveisViewTestCase(APITestCase):
    def setUp(self):
        self.prestador = User.objects.create_user(username="alice", password="123")
        self.url = "/api/horarios-disponiveis/?username=alice&data=2024-03-22"

    @mock.patch("agenda.views.get_horarios_disponiveis", return_value=[])
    def test_horarios_disponiveis_lista_vazia(self, mock_horarios):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data["horarios_disponiveis"] == []

    @mock.patch("agenda.views.get_horarios_disponiveis", return_value=["09:00", "10:00"])
    def test_horarios_disponiveis_com_horarios(self, mock_horarios):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert "09:00" in response.data["horarios_disponiveis"]

    def test_horarios_sem_parametros(self):
        response = self.client.get("/api/horarios-disponiveis/")
        assert response.status_code == 400

    def test_horarios_prestador_inexistente(self):
        response = self.client.get("/api/horarios-disponiveis/?username=inexistente&data=2024-03-22")
        assert response.status_code == 404

    def test_horarios_data_formato_invalido_linha_197(self):
        """Coverage linha 197: date.fromisoformat() falha"""
        response = self.client.get("/api/horarios-disponiveis/?username=alice&data=invalid-date")
        assert response.status_code == 400
        assert response.data["erro"] == "Data inválida. Use o formato YYYY-MM-DD."

class GetHorariosDisponiveisTestCase(APITestCase):
    def setUp(self):
        self.prestador = User.objects.create_user(username="alice", password="123")

    @mock.patch("agenda.utils.is_feriado", return_value=True)
    def test_retorna_vazio_em_feriado(self, mock_feriado):
        from agenda.utils import get_horarios_disponiveis
        resultado = get_horarios_disponiveis(date(2024, 1, 1), self.prestador)
        assert resultado == []

    @mock.patch("agenda.utils.is_feriado", return_value=False)
    def test_retorna_horarios_sem_agendamentos(self, mock_feriado):
        from agenda.utils import get_horarios_disponiveis
        resultado = get_horarios_disponiveis(date(2024, 3, 22), self.prestador)
        assert len(resultado) == 9

    @mock.patch("agenda.utils.is_feriado", return_value=False)
    def test_retorna_horarios_com_agendamento_ocupado(self, mock_feriado):
        from agenda.utils import get_horarios_disponiveis
        tz_brasil = timezone(timedelta(hours=-3))
        Agendamento.objects.create(
            data_horario=datetime(2024, 3, 22, 9, 0, tzinfo=tz_brasil),
            nome_cliente="Carl",
            email_cliente="carl@teste.com",
            telefone_cliente="+5521999978888",
            prestador=self.prestador
        )
        resultado = get_horarios_disponiveis(date(2024, 3, 22), self.prestador)
        assert "09:00" not in resultado
        assert len(resultado) == 8

    @mock.patch("agenda.utils.requests")
    def test_is_feriado_erro_na_api(self, mock_requests):
        from agenda.utils import is_feriado
        mock_requests.get.side_effect = Exception("Erro de conexão")
        resultado = is_feriado(date(2024, 1, 1))
        assert resultado is False


class EnderecoViewTestCase(APITestCase):
    def setUp(self):
        self.prestador = User.objects.create_user(username="alice", password="123")
        self.client.force_authenticate(user=self.prestador)
        self.url = "/api/prestadores/alice/enderecos/"

    @mock.patch("agenda.views.requests.get")
    def test_criar_endereco_com_cep_valido(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "state": "RJ",
            "city": "Rio de Janeiro",
            "neighborhood": "Flamengo",
            "street": "Rua dos Pinheiros",
        }
        data = {"cep": "22220050"}
        response = self.client.post(self.url, data)
        assert response.status_code == 201
        assert response.data["cidade"] == "Rio de Janeiro"

    @mock.patch("agenda.views.requests.get")
    def test_criar_endereco_com_cep_invalido(self, mock_get):
        mock_get.return_value.status_code = 404
        data = {"cep": "00000000"}
        response = self.client.post(self.url, data)
        assert response.status_code == 400

    def test_criar_endereco_sem_cep(self):
        response = self.client.post(self.url, {})
        assert response.status_code == 400

    def test_criar_endereco_prestador_inexistente(self):
        response = self.client.post("/api/prestadores/inexistente/enderecos/", {"cep": "22220050"})
        assert response.status_code == 404

    def test_criar_endereco_completo(self):
        data = {
            "cep": "22220050",
            "estado": "RJ",
            "cidade": "Rio de Janeiro",
            "bairro": "Flamengo",
            "rua": "Rua dos Pinheiros",
            "complemento": "100"
        }
        response = self.client.post(self.url, data)
        assert response.status_code == 201
        assert response.data["complemento"] == "100"

    @mock.patch("agenda.views.requests.get")
    def test_criar_endereco_cep_valido_mas_dados_invalidos(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "state": "",
            "city": "",
            "neighborhood": "",
            "street": "",
        }
        data = {"cep": "00000000"}
        response = self.client.post(self.url, data)
        assert response.status_code == 400    


# NOVOS TESTES - 100% COVERAGE!
class AgendamentoListCreateViewEdgeCases(APITestCase):
    """Coverage linha 32: Agendamento.objects.none()"""
    
    def setUp(self):
        self.prestador1 = User.objects.create_user(username="alice", password="123")
        self.cliente = User.objects.create_user(username="cliente", password="123")

    def test_get_queryset_returns_none_for_wrong_user(self):
        """Testa quando username != user logado (linha 32)"""
        self.client.force_authenticate(user=self.cliente)
        response = self.client.get('/api/agendamentos/?username=alice')
        assert response.status_code == 200
        assert len(response.data) == 0  # .none() executado

    def test_get_queryset_returns_none_sem_username(self):
        """Testa sem username param (linha 32)"""
        self.client.force_authenticate(user=self.prestador1)
        response = self.client.get('/api/agendamentos/')
        assert response.status_code == 200
        assert len(response.data) == 0