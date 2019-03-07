drop database if exists users;
create database users;
use users;

create table users(
	id int auto_increment,
	name varchar(255) not null,
	password varchar(255) not null,
	email varchar(255) not null,
	org varchar(255),

	primary key (id),
	constraint emailCheck check(email like '%@%')
);

create table productKey(
	id int auto_increment,
	activationKey varchar(255) not null,
	activationCount int not null default 0,
	userID int,

	primary key (id),
	foreign key (userID) references users(id)
);
