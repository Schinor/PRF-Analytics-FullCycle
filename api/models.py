from typing import Optional
from datetime import date, time, datetime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, Text, Integer, Numeric, Date, Time, DateTime, Boolean, ForeignKey, func


class Base(DeclarativeBase):
    pass


class UF(Base):
    __tablename__ = "UF"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)


class BR(Base):
    __tablename__ = "BR"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)


class Regional(Base):
    __tablename__ = "Regional"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    # Optional: nao aceita NOT NULL porque o script de carga nunca preenche "nome"
    nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Delegacia(Base):
    __tablename__ = "Delegacia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class UOP(Base):
    __tablename__ = "UOP"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sigla: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    nome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Arquivo_Carregado(Base):
    __tablename__ = "Arquivo_Carregado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    carregado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class Acidentes_Registrados(Base):
    __tablename__ = "Acidentes_Registrados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data_inversa: Mapped[Optional[date]] = mapped_column(Date)
    dia_semana: Mapped[Optional[str]] = mapped_column(String(15))
    horario: Mapped[Optional[time]] = mapped_column(Time)

    uf_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("UF.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    br_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("BR.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )

    km: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    municipio: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    causa_acidente: Mapped[Optional[str]] = mapped_column(Text)
    tipo_acidente: Mapped[Optional[str]] = mapped_column(String(60))
    classificacao_acidente: Mapped[Optional[str]] = mapped_column(String(30))
    fase_dia: Mapped[Optional[str]] = mapped_column(String(30))
    sentido_via: Mapped[Optional[str]] = mapped_column(String(15))
    condicao_metereologica: Mapped[Optional[str]] = mapped_column(String(60))
    tipo_pista: Mapped[Optional[str]] = mapped_column(String(60))
    tracado_via: Mapped[Optional[str]] = mapped_column(String(60))
    uso_solo: Mapped[Optional[str]] = mapped_column(String(30))
    pessoas: Mapped[Optional[int]] = mapped_column(Integer)
    mortos: Mapped[Optional[int]] = mapped_column(Integer)
    feridos_leves: Mapped[Optional[int]] = mapped_column(Integer)
    feridos_graves: Mapped[Optional[int]] = mapped_column(Integer)
    ilesos: Mapped[Optional[int]] = mapped_column(Integer)
    ignorados: Mapped[Optional[int]] = mapped_column(Integer)
    feridos: Mapped[Optional[int]] = mapped_column(Integer)
    veiculos: Mapped[Optional[int]] = mapped_column(Integer)

    regional_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("Regional.id", onupdate="SET NULL", ondelete="SET NULL")
    )
    delegacia_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("Delegacia.id", onupdate="SET NULL", ondelete="SET NULL")
    )
    uop_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("UOP.id", onupdate="SET NULL", ondelete="SET NULL")
    )

    is_fimdesemana: Mapped[bool] = mapped_column(Boolean, nullable=False)


# Observacao: a tabela "Usuario" do seu SQL original nao esta neste arquivo de
# models. Se ela ainda for necessaria no projeto, precisa ser adicionada aqui
# tambem -- do jeito que esta, Base.metadata.create_all() nao vai cria-la.