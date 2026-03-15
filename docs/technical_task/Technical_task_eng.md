# Technical Specification for the Course Project

**Author:** Artem Davydchuk

## Contents

1. Name and Scope of Application
2. Reasons for Development
3. Purpose and Objective of Development
4. Development Sources
5. Technical Requirements
   1. Requirements for the Developed Product
   2. Software Requirements
   3. Hardware Requirements
6. Development Stages

---

## 1. Name and Scope of Application

This technical specification applies to the development of the software application **"System for Dialog Interaction with Large Language Models with Web and Console Interfaces"**.

The scope of application of the developed software product includes: organization of user interaction with a language model, management of chat history, launching the application in different operating modes, as well as its use for educational, demonstration, and research purposes in the fields of information technology, artificial intelligence, and software engineering.

The software application is intended for local or network use on a personal computer and must provide convenient interaction with the system both through a browser-based web user interface and through a command-line interface.

## 2. Reasons for Development

The basis for development is the assignment for the course project within the educational and professional program **"Computer Systems and Networks"** in specialty **123 "Computer Engineering"**.

The need for development is due to the growing relevance of systems that provide interaction between humans and intelligent software tools, in particular with large language models, as well as by the need to create a convenient, flexible, and accessible software tool that supports multiple modes of operation: a web interface and a console interface.

## 3. Purpose and Objective of Development

The purpose of this project is to develop a software application for dialog interaction with a large language model, which provides:

- operation in two modes: through a browser-based web user interface and through a command-line interface (CLI);
- creation of a new chat and selection of an existing chat;
- input, transmission, and display of messages within a dialogue;
- storage of chat history;
- ease of use and clear organization of the interface.

The objective of the development is to create a universal software tool that can be used as a demonstration, educational, or basic applied system for working with language models and for further extension of functional capabilities.

## 4. Development Sources

The sources for development are:

- scientific and technical literature on software engineering, artificial intelligence, and the construction of dialogue systems;
- reference documentation for the Python programming language;
- documentation for libraries used to implement web and console interfaces;
- Internet publications devoted to the construction of LLM systems, client applications, and user interfaces;
- materials on software architecture design and data storage organization.

## 5. Technical Requirements

### 5.1 Requirements for the Developed Product

The developed software application must meet the following requirements:

1. The program must be launched from the main file `app.py`.
2. Two modes of operation must be implemented:
   - standard launch — launching the web user interface accessible through a browser;
   - launch with the `-t` parameter — switching to command-line mode.
3. In web interface mode, the following must be provided:
   - display of the chat list;
   - creation of a new chat;
   - opening an existing chat;
   - display of message history;
   - input of a new message and receipt of a response.
4. In console mode, the following must be provided:
   - creation of a new chat;
   - selection of an existing chat;
   - exchange of messages in text mode;
   - correct termination of the session.
5. Chat history storage in files or local data storage must be implemented.
6. The program interface must be logically structured, understandable, and convenient for the user.
7. The program must correctly handle input errors, startup failures, and invalid command-line parameters.
8. The software architecture must allow for further extension of functionality.

### 5.2 Software Requirements

The following are required for the functioning of the software application:

- operating system: Windows 10/11, Linux, or another modern operating system with Python support;
- Python interpreter version 3.10 or higher;
- a modern web browser with support for HTML5, CSS, and JavaScript;
- libraries and modules required to implement the web user interface, program logic, and chat history storage;
- software development and debugging tools, if necessary.

### 5.3 Hardware Requirements

For operation of the software application, a personal computer is required with the following minimum characteristics:

- x86_64 architecture processor;
- RAM — at least 8 GB;
- free disk space — at least 1 GB;
- monitor, keyboard, and input device;
- if necessary, Internet connection for working with external services or models.

## 6. Development Stages

| No. | Development Stage | Date |
|---|---|---|
| 6.1 | Receiving the topic and assignment | 15.02.2026 |
| 6.2 | Selection and study of literature on dialogue systems, LLMs, and web user interfaces | 15.03.2026 |
| 6.3 | Preparation of the technical specification | 15.03.2026 |
| 6.4 | Analysis of the subject area and review of existing approaches to building dialogue applications |  |
| 6.5 | Designing the structure of the software application, web interface and CLI modes, as well as the chat storage mechanism |  |
| 6.6 | Development of the software application |  |
| 6.7 | Testing of the software application |  |
| 6.8 | Preparation of the explanatory note |  |
| 6.9 | Submission of the course project (paper) for review |  |
| 6.10 | Defense of the course project (paper) |  |