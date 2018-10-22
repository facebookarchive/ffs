-- Copyright (c) Facebook, Inc. and its affiliates.
-- All rights reserved.
--
-- This source code is licensed under the BSD-style license found in the
-- LICENSE file in the root directory of this source tree.

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.13
-- Dumped by pg_dump version 9.5.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE piponger;
--
-- Name: piponger; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE piponger WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


ALTER DATABASE piponger OWNER TO postgres;

\connect piponger

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: allocated_pinger_port; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.allocated_pinger_port (
    address text NOT NULL,
    port integer NOT NULL
);


ALTER TABLE public.allocated_pinger_port OWNER TO piponger_user;

--
-- Name: iperf_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.iperf_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.iperf_id_seq OWNER TO piponger_user;

--
-- Name: iperf; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.iperf (
    id integer DEFAULT nextval('public.iperf_id_seq'::regclass) NOT NULL,
    pinger_iteration_id integer,
    status text,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    result text,
    ponger_port_id integer NOT NULL,
    src_port integer NOT NULL
);


ALTER TABLE public.iperf OWNER TO piponger_user;

--
-- Name: pinger_iteration; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.pinger_iteration (
    id integer NOT NULL,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    status text,
    remote_id text NOT NULL,
    remote_address text NOT NULL,
    tracert_qty integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.pinger_iteration OWNER TO piponger_user;

--
-- Name: iteration_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.iteration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.iteration_id_seq OWNER TO piponger_user;

--
-- Name: iteration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.iteration_id_seq OWNED BY public.pinger_iteration.id;


--
-- Name: master_iteration; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.master_iteration (
    id integer NOT NULL,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    status text DEFAULT 'CREATED'::text NOT NULL
);


ALTER TABLE public.master_iteration OWNER TO piponger_user;

--
-- Name: master_iteration_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.master_iteration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.master_iteration_id_seq OWNER TO piponger_user;

--
-- Name: master_iteration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.master_iteration_id_seq OWNED BY public.master_iteration.id;


--
-- Name: master_iteration_pinger; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.master_iteration_pinger (
    id integer NOT NULL,
    master_iteration_id integer,
    registered_pinger_id integer NOT NULL,
    status text,
    result text,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    last_updated_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.master_iteration_pinger OWNER TO piponger_user;

--
-- Name: master_iteration_pinger_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.master_iteration_pinger_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.master_iteration_pinger_id_seq OWNER TO piponger_user;

--
-- Name: master_iteration_pinger_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.master_iteration_pinger_id_seq OWNED BY public.master_iteration_pinger.id;


--
-- Name: master_iteration_result; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.master_iteration_result (
    id integer NOT NULL,
    master_iteration_id integer NOT NULL,
    problematic_host text,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    score numeric
);


ALTER TABLE public.master_iteration_result OWNER TO piponger_user;

--
-- Name: master_iteration_result_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.master_iteration_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.master_iteration_result_id_seq OWNER TO piponger_user;

--
-- Name: master_iteration_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.master_iteration_result_id_seq OWNED BY public.master_iteration_result.id;


--
-- Name: pinger_iteration_status_type; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.pinger_iteration_status_type (
    type_id text NOT NULL
);


ALTER TABLE public.pinger_iteration_status_type OWNER TO piponger_user;

--
-- Name: ponger; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.ponger (
    id integer NOT NULL,
    address text,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    pinger_iteration_id integer NOT NULL,
    api_port integer,
    api_protocol text
);


ALTER TABLE public.ponger OWNER TO piponger_user;

--
-- Name: ponger_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.ponger_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ponger_id_seq OWNER TO piponger_user;

--
-- Name: ponger_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.ponger_id_seq OWNED BY public.ponger.id;


--
-- Name: ponger_port; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.ponger_port (
    ponger_id integer NOT NULL,
    src_port_min integer,
    id integer NOT NULL,
    dst_port integer,
    src_port_max integer
);


ALTER TABLE public.ponger_port OWNER TO piponger_user;

--
-- Name: ponger_port_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.ponger_port_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ponger_port_id_seq OWNER TO piponger_user;

--
-- Name: ponger_port_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.ponger_port_id_seq OWNED BY public.ponger_port.id;


--
-- Name: registered_pinger_nodes; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.registered_pinger_nodes (
    id integer NOT NULL,
    address text NOT NULL,
    api_protocol text NOT NULL,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    api_port integer NOT NULL,
    last_updated_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.registered_pinger_nodes OWNER TO piponger_user;

--
-- Name: registrered_ponger_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.registrered_ponger_nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.registrered_ponger_nodes_id_seq OWNER TO piponger_user;

--
-- Name: registered_ponger_nodes; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.registered_ponger_nodes (
    id integer DEFAULT nextval('public.registrered_ponger_nodes_id_seq'::regclass) NOT NULL,
    address text NOT NULL,
    api_protocol text NOT NULL,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    api_port integer NOT NULL,
    last_updated_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.registered_ponger_nodes OWNER TO piponger_user;

--
-- Name: registrered_pinger_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.registrered_pinger_nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.registrered_pinger_nodes_id_seq OWNER TO piponger_user;

--
-- Name: registrered_pinger_nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.registrered_pinger_nodes_id_seq OWNED BY public.registered_pinger_nodes.id;


--
-- Name: task_status_type; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.task_status_type (
    type_id text NOT NULL
);


ALTER TABLE public.task_status_type OWNER TO piponger_user;

--
-- Name: tracert; Type: TABLE; Schema: public; Owner: piponger_user
--

CREATE TABLE public.tracert (
    id integer NOT NULL,
    pinger_iteration_id integer,
    status text,
    created_date timestamp without time zone DEFAULT now() NOT NULL,
    result text,
    ponger_port_id integer NOT NULL
);


ALTER TABLE public.tracert OWNER TO piponger_user;

--
-- Name: tracert_id_seq; Type: SEQUENCE; Schema: public; Owner: piponger_user
--

CREATE SEQUENCE public.tracert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tracert_id_seq OWNER TO piponger_user;

--
-- Name: tracert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piponger_user
--

ALTER SEQUENCE public.tracert_id_seq OWNED BY public.tracert.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration ALTER COLUMN id SET DEFAULT nextval('public.master_iteration_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_pinger ALTER COLUMN id SET DEFAULT nextval('public.master_iteration_pinger_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_result ALTER COLUMN id SET DEFAULT nextval('public.master_iteration_result_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.pinger_iteration ALTER COLUMN id SET DEFAULT nextval('public.iteration_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger ALTER COLUMN id SET DEFAULT nextval('public.ponger_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger_port ALTER COLUMN id SET DEFAULT nextval('public.ponger_port_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.registered_pinger_nodes ALTER COLUMN id SET DEFAULT nextval('public.registrered_pinger_nodes_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.tracert ALTER COLUMN id SET DEFAULT nextval('public.tracert_id_seq'::regclass);


--
-- Data for Name: pinger_iteration_status_type; Type: TABLE DATA; Schema: public; Owner: piponger_user
--

INSERT INTO public.pinger_iteration_status_type VALUES ('CREATED');
INSERT INTO public.pinger_iteration_status_type VALUES ('RUNNING');
INSERT INTO public.pinger_iteration_status_type VALUES ('FINISHED');
INSERT INTO public.pinger_iteration_status_type VALUES ('ERROR');


--
-- Data for Name: task_status_type; Type: TABLE DATA; Schema: public; Owner: piponger_user
--

INSERT INTO public.task_status_type VALUES ('PENDING');
INSERT INTO public.task_status_type VALUES ('STARTED');
INSERT INTO public.task_status_type VALUES ('SUCCESS');
INSERT INTO public.task_status_type VALUES ('FAILURE');
INSERT INTO public.task_status_type VALUES ('RETRY');
INSERT INTO public.task_status_type VALUES ('REVOKED');


--
-- Name: iperf_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.iperf
    ADD CONSTRAINT iperf_pkey PRIMARY KEY (id);


--
-- Name: iteration_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.pinger_iteration
    ADD CONSTRAINT iteration_pkey PRIMARY KEY (id);


--
-- Name: iteration_remote_id_key; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.pinger_iteration
    ADD CONSTRAINT iteration_remote_id_key UNIQUE (remote_id);


--
-- Name: iteration_type_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.pinger_iteration_status_type
    ADD CONSTRAINT iteration_type_pkey PRIMARY KEY (type_id);


--
-- Name: master_iteration_pinger_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_pinger
    ADD CONSTRAINT master_iteration_pinger_pkey PRIMARY KEY (id);


--
-- Name: master_iteration_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration
    ADD CONSTRAINT master_iteration_pkey PRIMARY KEY (id);


--
-- Name: master_iteration_result_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_result
    ADD CONSTRAINT master_iteration_result_pkey PRIMARY KEY (id);


--
-- Name: pinger_port_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.allocated_pinger_port
    ADD CONSTRAINT pinger_port_pkey PRIMARY KEY (address);


--
-- Name: ponger_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger
    ADD CONSTRAINT ponger_pkey PRIMARY KEY (id);


--
-- Name: ponger_port_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger_port
    ADD CONSTRAINT ponger_port_pkey PRIMARY KEY (id);


--
-- Name: registrered_pinger_nodes_address_port_key; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.registered_pinger_nodes
    ADD CONSTRAINT registrered_pinger_nodes_address_port_key UNIQUE (address, api_port);


--
-- Name: registrered_pinger_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.registered_pinger_nodes
    ADD CONSTRAINT registrered_pinger_nodes_pkey PRIMARY KEY (id);


--
-- Name: registrered_ponger_nodes_address_port_key; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.registered_ponger_nodes
    ADD CONSTRAINT registrered_ponger_nodes_address_port_key UNIQUE (address, api_port);


--
-- Name: registrered_ponger_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.registered_ponger_nodes
    ADD CONSTRAINT registrered_ponger_nodes_pkey PRIMARY KEY (id);


--
-- Name: status_type_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.task_status_type
    ADD CONSTRAINT status_type_pkey PRIMARY KEY (type_id);


--
-- Name: tracert_pkey; Type: CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.tracert
    ADD CONSTRAINT tracert_pkey PRIMARY KEY (id);


--
-- Name: iperf_iteration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.iperf
    ADD CONSTRAINT iperf_iteration_id_fkey FOREIGN KEY (pinger_iteration_id) REFERENCES public.pinger_iteration(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: iperf_ponger_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.iperf
    ADD CONSTRAINT iperf_ponger_port_id_fkey FOREIGN KEY (ponger_port_id) REFERENCES public.ponger_port(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: iperf_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.iperf
    ADD CONSTRAINT iperf_status_fkey FOREIGN KEY (status) REFERENCES public.task_status_type(type_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: iteration_status_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.pinger_iteration
    ADD CONSTRAINT iteration_status_fkey1 FOREIGN KEY (status) REFERENCES public.pinger_iteration_status_type(type_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: master_iteration_pinger_master_iteration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_pinger
    ADD CONSTRAINT master_iteration_pinger_master_iteration_id_fkey FOREIGN KEY (master_iteration_id) REFERENCES public.master_iteration(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: master_iteration_pinger_registered_pinger_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_pinger
    ADD CONSTRAINT master_iteration_pinger_registered_pinger_id_fkey FOREIGN KEY (registered_pinger_id) REFERENCES public.registered_pinger_nodes(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: master_iteration_pinger_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_pinger
    ADD CONSTRAINT master_iteration_pinger_status_fkey FOREIGN KEY (status) REFERENCES public.pinger_iteration_status_type(type_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: master_iteration_result_master_iteration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration_result
    ADD CONSTRAINT master_iteration_result_master_iteration_id_fkey FOREIGN KEY (master_iteration_id) REFERENCES public.master_iteration(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: master_iteration_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.master_iteration
    ADD CONSTRAINT master_iteration_status_fkey FOREIGN KEY (status) REFERENCES public.pinger_iteration_status_type(type_id);


--
-- Name: ponger_iteration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger
    ADD CONSTRAINT ponger_iteration_id_fkey FOREIGN KEY (pinger_iteration_id) REFERENCES public.pinger_iteration(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ponger_port_ponger_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.ponger_port
    ADD CONSTRAINT ponger_port_ponger_id_fkey FOREIGN KEY (ponger_id) REFERENCES public.ponger(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tracert_iteration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.tracert
    ADD CONSTRAINT tracert_iteration_id_fkey FOREIGN KEY (pinger_iteration_id) REFERENCES public.pinger_iteration(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tracert_ponger_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.tracert
    ADD CONSTRAINT tracert_ponger_port_id_fkey FOREIGN KEY (ponger_port_id) REFERENCES public.ponger_port(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tracert_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piponger_user
--

ALTER TABLE ONLY public.tracert
    ADD CONSTRAINT tracert_status_fkey FOREIGN KEY (status) REFERENCES public.task_status_type(type_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--
