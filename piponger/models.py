#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
This file contains the database model definitions for the piponger node
It includes all node data:
    Master, pinger and ponger tables

The tables have extra relationships to back_populate data without
making new explicit queries (back_populates)
"""

# coding: utf-8
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, Text,
                        UniqueConstraint, text)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AllocatedPingerPort(Base):
    __tablename__ = 'allocated_pinger_port'

    address = Column(Text, primary_key=True)
    port = Column(Integer, nullable=False)


class Iperf(Base):
    __tablename__ = 'iperf'

    id = Column(Integer, primary_key=True)
    pinger_iteration_id = Column(
        ForeignKey(
            'pinger_iteration.id', ondelete='CASCADE', onupdate='CASCADE'))
    status = Column(
        ForeignKey(
            'task_status_type.type_id', ondelete='CASCADE',
            onupdate='CASCADE'))
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    result = Column(Text)
    ponger_port_id = Column(
        ForeignKey('ponger_port.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)
    src_port = Column(Integer, nullable=False)

    pinger_iteration = relationship('PingerIteration', back_populates='iperf')
    ponger_port = relationship('PongerPort')
    task_status_type = relationship('TaskStatusType')


class MasterIteration(Base):
    __tablename__ = 'master_iteration'

    id = Column(Integer, primary_key=True)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    status = Column(
        ForeignKey('pinger_iteration_status_type.type_id'),
        nullable=False,
        server_default=text("'CREATED'::text"))
    json_graph = Column(Text)

    master_iteration_pinger = relationship(
        'MasterIterationPinger', back_populates='master_iteration')
    master_iteration_result = relationship(
        'MasterIterationResult', back_populates='master_iteration')


class MasterIterationPinger(Base):
    __tablename__ = 'master_iteration_pinger'

    id = Column(Integer, primary_key=True)
    master_iteration_id = Column(
        ForeignKey(
            'master_iteration.id', ondelete='CASCADE', onupdate='CASCADE'))
    registered_pinger_id = Column(
        ForeignKey(
            'registered_pinger_nodes.id',
            ondelete='CASCADE',
            onupdate='CASCADE'),
        nullable=False)
    status = Column(
        ForeignKey(
            'pinger_iteration_status_type.type_id',
            ondelete='CASCADE',
            onupdate='CASCADE'))
    result = Column(Text)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    last_updated_date = Column(
        DateTime, nullable=False, server_default=text("now()"))

    master_iteration = relationship(
        'MasterIteration', back_populates='master_iteration_pinger')
    registered_pinger = relationship('RegisteredPingerNode')
    pinger_iteration_status_type = relationship('PingerIterationStatusType')


class MasterIterationResult(Base):
    __tablename__ = 'master_iteration_result'

    id = Column(Integer, primary_key=True)
    master_iteration_id = Column(
        ForeignKey(
            'master_iteration.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)
    problematic_host = Column(Text)
    score = Column(Numeric)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))

    master_iteration = relationship(
        'MasterIteration', back_populates='master_iteration_result')


class PingerIteration(Base):
    __tablename__ = 'pinger_iteration'

    id = Column(Integer, primary_key=True)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    status = Column(
        ForeignKey(
            'pinger_iteration_status_type.type_id',
            ondelete='CASCADE',
            onupdate='CASCADE'))
    remote_id = Column(Text, nullable=False, unique=True)
    remote_address = Column(Text, nullable=False)
    tracert_qty = Column(Integer, nullable=False, server_default=text("1"))

    pinger_iteration_status_type = relationship('PingerIterationStatusType')
    ponger = relationship('Ponger', back_populates='pinger_iteration')
    tracert = relationship('Tracert', back_populates='pinger_iteration')
    iperf = relationship('Iperf', back_populates='pinger_iteration')


class PingerIterationStatusType(Base):
    __tablename__ = 'pinger_iteration_status_type'

    type_id = Column(Text, primary_key=True)


class Ponger(Base):
    __tablename__ = 'ponger'

    id = Column(Integer, primary_key=True)
    address = Column(Text)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    pinger_iteration_id = Column(
        ForeignKey(
            'pinger_iteration.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)
    api_port = Column(Integer)
    api_protocol = Column(Text)

    pinger_iteration = relationship('PingerIteration', back_populates='ponger')
    ponger_port = relationship('PongerPort', back_populates='ponger')


class PongerPort(Base):
    __tablename__ = 'ponger_port'

    ponger_id = Column(
        ForeignKey('ponger.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)
    src_port_min = Column(Integer)
    id = Column(Integer, primary_key=True)
    dst_port = Column(Integer)
    src_port_max = Column(Integer)

    ponger = relationship('Ponger')


class RegisteredPingerNode(Base):
    __tablename__ = 'registered_pinger_nodes'
    __table_args__ = (UniqueConstraint('address', 'api_port'), )

    id = Column(Integer, primary_key=True)
    address = Column(Text, nullable=False)
    api_protocol = Column(Text, nullable=False)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    api_port = Column(Integer, nullable=False)
    last_updated_date = Column(
        DateTime, nullable=False, server_default=text("now()"))


class RegisteredPongerNode(Base):
    __tablename__ = 'registered_ponger_nodes'
    __table_args__ = (UniqueConstraint('address', 'api_port'), )

    id = Column(Integer, primary_key=True)
    address = Column(Text, nullable=False)
    api_protocol = Column(Text, nullable=False)
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    api_port = Column(Integer, nullable=False)
    last_updated_date = Column(
        DateTime, nullable=False, server_default=text("now()"))


class TaskStatusType(Base):
    __tablename__ = 'task_status_type'

    type_id = Column(Text, primary_key=True)


class Tracert(Base):
    __tablename__ = 'tracert'

    id = Column(Integer, primary_key=True)
    pinger_iteration_id = Column(
        ForeignKey(
            'pinger_iteration.id', ondelete='CASCADE', onupdate='CASCADE'))
    status = Column(
        ForeignKey(
            'task_status_type.type_id', ondelete='CASCADE',
            onupdate='CASCADE'))
    created_date = Column(
        DateTime, nullable=False, server_default=text("now()"))
    result = Column(Text)
    ponger_port_id = Column(
        ForeignKey('ponger_port.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)

    pinger_iteration = relationship(
        'PingerIteration', back_populates='tracert')
    ponger_port = relationship('PongerPort')
    task_status_type = relationship('TaskStatusType')
