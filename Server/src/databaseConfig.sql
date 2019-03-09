drop database if exists users;
create database users;
use users;

create table users(
	id int auto_increment,
	username varchar(32) not null,
	password varchar(128) not null,
	email varchar(254) not null,

	primary key (id),
	constraint emailCheck check(email like '%@%')
);

create table productKey(
	id int auto_increment,
	activationKey varchar(32) not null,
	activationCount int not null default 0,
	userID int,

	primary key (id),
	foreign key (userID) references users(id)
);
