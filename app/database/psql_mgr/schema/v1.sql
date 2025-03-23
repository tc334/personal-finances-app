create type access_levels as enum('ADMIN', 'USER');
create type storage_status as enum('AVAILABLE', 'DELETED', 'NEVER_EXISTED');
create type account_type as enum('ASSET_LONGTERM', 'ASSET_SHORTTERM', 'ASSET_PREPAY', 'EXPENSE_OPERATING', 'INCOME', 'EQUITY', 'LIABILITY', 'RETAINED_EARNINGS', 'INCOME_SUMMARY');
create type account_permanence as enum('PERMANENT', 'TEMPORARY');
create type account_actions as enum('DEBIT', 'CREDIT');

create table person (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hashed_password CHAR(88) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL,
  level access_levels DEFAULT 'USER'
);

create table entity(
  id UUID PRIMARY KEY,
  name TEXT NOT NULL
);

create table person_entity_junction(
  user_id UUID REFERENCES person(id),
  entity_id UUID REFERENCES entity(id)
 );

 create table account(
   id UUID PRIMARY KEY,
   entity_id UUID REFERENCES entity(id),
   name TEXT NOT NULL,
   parent_account_id UUID,
   archived BOOLEAN DEFAULT 'FALSE',
   type account_type NOT NULL,
   permanence account_permanence NOT NULL,
   UNIQUE(id, type)
 );

create table journal(
   id UUID PRIMARY KEY,
   timestamp DATE NOT NULL,
   created_by UUID REFERENCES person(id),
   entity_id UUID REFERENCES entity(id),
   description TEXT NOT NULL,
   receipt_status storage_status NOT NULL DEFAULT 'NEVER_EXISTED'
 );

create table ledger(
   id UUID PRIMARY KEY,
   journal_id UUID NOT NULL REFERENCES journal(id),
   account_id UUID NOT NULL REFERENCES account(id),
   amount NUMERIC(2) NOT NULL,
   direction account_actions NOT NULL,
   reconciled BOOLEAN NOT NULL DEFAULT 'FALSE'
);

create table prepaid(
  id UUID PRIMARY KEY,
  amount NUMERIC(2) NOT NULL,
  receive_month DATE NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT 'FALSE',
  original_journal_id UUID REFERENCES journal(id),
  asset_account_id UUID NOT NULL,
  expense_account_id UUID NOT NULL,
  asset_account_type account_type NOT NULL,
  expense_account_type account_type NOT NULL,
  FOREIGN KEY (asset_account_id, asset_account_type) REFERENCES account(id, type),
  FOREIGN KEY (expense_account_id, expense_account_type) REFERENCES account(id, type),
  CHECK (asset_account_type = 'ASSET_PREPAY'),
  CHECK (expense_account_type = 'EXPENSE_OPERATING')
);
