**DATABASE**
- SQL editor codes to create tables.

----- Users -----

create table public.users (
  id uuid not null default gen_random_uuid (),
  name character varying(50) not null,
  email character varying(255) not null,
  hashed_password character varying(255) not null,
  phone character varying(20) null,
  company_id integer not null,
  role character varying(20) not null,
  is_active boolean not null default true,
  created_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email),
  constraint fk_company foreign KEY (company_id) references company (id) on delete RESTRICT
) TABLESPACE pg_default;

create trigger users_updated_at_trigger BEFORE
update on users for EACH row
execute FUNCTION update_updated_at_column ();


----- Company Service -----
create table public.company_service (
  id serial not null,
  company_id integer not null,
  name character varying(100) not null,
  description text null,
  price numeric(10, 2) not null default 0.00,
  duration_minutes integer not null default 30,
  is_active boolean not null default true,
  created_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  constraint company_service_pkey primary key (id),
  constraint uq_company_service_name_company_id unique (company_id, name),
  constraint fk_company_service_company foreign KEY (company_id) references company (id) on delete CASCADE
) TABLESPACE pg_default;

----- Company -----
create table public.company (
  id serial not null,
  name character varying(100) not null,
  phone character varying(20) null,
  email character varying(255) null,
  address character varying(255) null,
  is_active boolean not null default true,
  created_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  constraint company_pkey primary key (id),
  constraint company_email_key unique (email),
  constraint company_name_key unique (name)
) TABLESPACE pg_default;

create trigger company_updated_at_trigger BEFORE
update on company for EACH row
execute FUNCTION update_updated_at_column ();

----- Appointments -----

create table public.appointments (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  company_id integer not null,
  appointment_time timestamp with time zone not null,
  end_time timestamp with time zone not null,
  status character varying(20) not null default 'scheduled'::character varying,
  notes text null,
  created_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone not null default CURRENT_TIMESTAMP,
  constraint appointments_pkey primary key (id),
  constraint fk_appointments_company foreign KEY (company_id) references company (id) on delete CASCADE,
  constraint fk_appointments_user foreign KEY (user_id) references users (id) on delete CASCADE,
  constraint chk_appointment_time_order check ((appointment_time < end_time))
) TABLESPACE pg_default;

----- Appointment Service -----
create table public.appointment_service (
  appointment_id uuid not null,
  company_service_id integer not null,
  quantity integer not null default 1,
  price_at_booking numeric(10, 2) not null,
  constraint appointment_service_pkey primary key (appointment_id, company_service_id),
  constraint fk_app_service_appointment foreign KEY (appointment_id) references appointments (id) on delete CASCADE,
  constraint fk_app_service_company_service foreign KEY (company_service_id) references company_service (id) on delete RESTRICT
) TABLESPACE pg_default;