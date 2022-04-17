--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    username text,
    email text,
    address text,
    city text,
    state text,
    password text,
    zip text,
    community text,
    name text,
    role text,
    county text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY users (username, email, address, city, state, password, zip, community, name, role, county) FROM stdin;
JoBlo	joblo@email.com	61 Spring RD	Lagunitas	CA	abc	94980	Lagunitas FPA	Joseph Blow	member	marin
Jdoe	Jdoe@email.com	50 Spring RD.	Lagunitas	CA	abc	94980	Lagunitas FPA	John Doe	member	marin
Philmore	Pmore@email.com	100 Lagunitas RD	Lagunitas	CA	abc	94980	Lagunitas FPA	Phil Moew	leader	marin
Bsmythe	Bsmythe@email.com	51 Maple LN	Lagunitas	CA	abc	94980	Lagunitas FPA	Bob Smythe	member	marin
Rgrant	Rgrant@email.com	130 Lagunitas RD	Lagunitas	CA	abc	94980	Lagunitas FPA	Roger Grant	member	marin
Bbly	Bbly@email.com	95 Mountain View AVE	Lagunitas	CA	abc	94980	Lagunitas FPA	Bill Bly	member	marin
Ifewell	Ifewell@email.com	125 Mountain View AVE	Lagunitas	CA	abc	94980	Lagunitas FPA	Irma Fewell	member	marin
Bdunt	Bdunt@email.com	3 Chimney LN	Lagunitas	CA	abc	94980	Lagunitas FPA	Betty Dunt	member	marin
jwhatever	joblo@abc.com	23235 TOKAYANA WAY	Colfax	CA	abc	95713	colfax firewise	JoBlo Whatever	member	Placer
\.


--
-- PostgreSQL database dump complete
--

