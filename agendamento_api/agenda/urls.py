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
    path("agendamentos/", AgendamentoListCreateView.as_view(), name="agendamento-list-create"),
    path("agendamentos/<int:pk>/", AgendamentoDetailView.as_view(), name="agendamento-detail"),
    path("agendamentos/<int:pk>/confirmar/", AgendamentoConfirmarView.as_view(), name="agendamento-confirmar"),
    path("agendamentos/<int:pk>/executar/", AgendamentoExecutarView.as_view(), name="agendamento-executar"),
    path("horarios-disponiveis/", HorariosDisponiveisView.as_view(), name="horarios-disponiveis"),
    path("prestadores/<str:username>/enderecos/", EnderecoView.as_view(), name="prestador-endereco"),
]