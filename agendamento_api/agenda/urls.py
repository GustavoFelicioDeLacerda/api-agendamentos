from django.urls import path
from .views import (
    AgendamentoListCreateView,
    AgendamentoDetailView,
    AgendamentoConfirmarView,
    AgendamentoExecutarView,
    HorariosDisponiveisView,
    EnderecoView,
)

urlpatterns = [

    # CRUD de agendamentos
    path(
        "agendamentos/",
        AgendamentoListCreateView.as_view(),
        name="agendamento-list-create"
    ),

    path(
        "agendamentos/<int:pk>/",
        AgendamentoDetailView.as_view(),
        name="agendamento-detail"
    ),

    # ações do agendamento
    path(
        "agendamentos/<int:pk>/confirmar/",
        AgendamentoConfirmarView.as_view(),
        name="agendamento-confirmar"
    ),

    path(
        "agendamentos/<int:pk>/executar/",
        AgendamentoExecutarView.as_view(),
        name="agendamento-executar"
    ),

    # consulta de horários
    path(
        "horarios-disponiveis/",
        HorariosDisponiveisView.as_view(),
        name="horarios-disponiveis"
    ),

    # endereço do prestador
    path(
        "prestadores/<str:username>/enderecos/",
        EnderecoView.as_view(),
        name="prestador-endereco"
    ),

]