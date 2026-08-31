# Academic Assistant with Smart Lecture Recording and Intelligent Indexing System

A web-based academic assistant designed to help lecturers and students manage lecture recordings, automatically transcribe lecture audio, generate summaries, identify important topics, navigate recordings through timestamps, and manage academic schedules.

The system combines **Django**, **SQLite**, **Faster-Whisper**, and natural language processing techniques to transform ordinary lecture recordings into searchable and structured academic resources.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Features](#features)
- [User Roles](#user-roles)
- [System Workflow](#system-workflow)
- [Technologies Used](#technologies-used)
- [Project Architecture](#project-architecture)
- [Project Structure](#project-structure)
- [Core Modules](#core-modules)
- [Lecture Processing Pipeline](#lecture-processing-pipeline)
- [Smart Lecture Recording](#smart-lecture-recording)
- [Lecture Upload](#lecture-upload)
- [Speech-to-Text Transcription](#speech-to-text-transcription)
- [Timestamp Navigation](#timestamp-navigation)
- [Topic Indexing](#topic-indexing)
- [Lecture Summarization](#lecture-summarization)
- [Courses](#courses)
- [Timetable and Reminders](#timetable-and-reminders)
- [Dashboard](#dashboard)
- [Profile Management](#profile-management)
- [Authentication and Authorization](#authentication-and-authorization)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Challenges Encountered](#challenges-encountered)
- [Future Improvements](#future-improvements)

---

## Overview

The Academic Assistant is a Django-based application that helps transform lecture recordings into useful academic material.

Instead of requiring students to manually search through long audio recordings, the system processes lecture audio and provides:

- Automatic speech-to-text transcription
- Timestamped transcript segments
- Lecture topic identification
- Topic timestamps
- Automatic lecture summaries
- Key points
- Searchable transcripts
- Clickable timestamps for navigating recordings
- Course management
- Timetable management
- Upcoming class reminders
- Lecture recording and upload functionality

The system is designed around the idea that a recorded lecture should be more than an audio file. It should become an indexed and searchable academic resource.

---

## Problem Statement

Students frequently record lectures for later revision, but finding a particular explanation inside a long recording can be difficult.

For example, a student may remember that a lecturer explained **Lexical Analysis** during a Compiler Design lecture but may not remember where that explanation occurred in a one-hour recording.

The student would normally have to manually seek through the entire recording.

The Academic Assistant solves this problem by converting the lecture into structured information containing:

- Transcript
- Timestamps
- Topics
- Summary
- Key points

The user can therefore locate important sections of a lecture without manually searching through the entire recording.

---

## Objectives

The major objectives of the project are to:

1. Develop a web-based academic assistant for lecturers and students.
2. Allow lecturers to record lectures directly from the browser.
3. Allow lecturers to upload existing lecture recordings.
4. Automatically convert speech in lecture recordings into text.
5. Generate timestamped transcript segments.
6. identify important topics discussed during lectures.
7. Associate identified topics with their corresponding timestamps.
8. Generate concise lecture summaries and key points.
9. Allow users to search lecture transcripts.
10. Allow users to click timestamps and jump directly to the corresponding section of the recording.
11. Provide course management functionality.
12. Provide personal timetable management.
13. Display upcoming classes and reminders.
14. Enforce different permissions for lecturers and students.

---

# Features

## Lecture Management

- Record lectures directly from the browser
- Upload existing lecture audio files
- Store lecture recordings
- View previously processed lectures
- Delete lectures
- Reprocess lectures
- View lecture processing status
- Search lectures
- Filter lectures by course
- Filter lectures by date
- Filter lectures by processing status

## Intelligent Lecture Processing

- Speech-to-text transcription
- Timestamped transcription
- Topic extraction
- Topic indexing
- Lecture summarization
- Key point generation
- Searchable transcripts
- Clickable timestamps
- Audio seeking from transcript timestamps
- Audio seeking from topic timestamps

## Academic Management

- Course creation and management
- Course-specific lecture pages
- Personal timetable
- Add classes to timetable
- Today's class schedule
- Upcoming class calculation
- Class reminders
- Dashboard statistics

## Account Features

- Student and lecturer accounts
- Authentication
- Role-based permissions
- Profile management
- Academic information
- Password management
- Secure logout

---

# User Roles

The application supports two primary user roles.

## Lecturer

Lecturers can:

- Create and manage courses
- Record lectures
- Upload lecture recordings
- Process lecture recordings
- Reprocess failed or completed recordings
- Delete their lectures
- View transcripts
- View lecture summaries
- View indexed topics
- Search lecture content
- Manage their timetable
- View upcoming classes

Only lecturers are allowed to create lecture recordings.

## Student

Students can:

- Browse available lectures
- Listen to lecture recordings
- Read transcripts
- Search transcripts
- View indexed topics
- View summaries
- Use timestamp navigation
- Browse courses
- Create and manage their personal timetable
- View upcoming classes and reminders

Students cannot record or upload lectures.

These permissions are enforced in both the user interface and the Django backend.

---

# System Workflow

The main lecture processing workflow is:

```text
Lecturer
   |
   v
Record Lecture / Upload Audio
   |
   v
Django Backend
   |
   v
Store Audio Recording
   |
   v
Speech Recognition
   |
   v
Faster-Whisper
   |
   v
Transcript
   |
   +--------------------+
   |                    |
   v                    v
Timestamp Segments    NLP Processing
                        |
                +-------+-------+
                |               |
                v               v
             Topics          Summary
                |               |
                v               v
          Topic Index       Key Points
                |
                v
          SQLite Database
                |
                v
         Lecture Detail Page