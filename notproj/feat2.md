- **Core:** Global settings, middleware, and basic user/account management.
- **Data_Engine:** Handles multi‑source data aggregation, parsing, and AI processing (including the chat interface).
- **Notifier:** Manages notification delivery and user personalization (preferences and alert rules).

---

## **Feature 1: Multi‑Source Data Aggregation and Parsing**

**Objective:**  
Automatically fetch notifications and related documents (HTML pages and PDFs) from various official sources and extract key raw information.

**What We Are Doing:**  
- **Web Scraping:** Periodically crawling designated websites to retrieve HTML notifications.  
- **PDF Parsing:** Downloading and extracting text from PDF documents (e.g., exam forms, registration notices).  
- **Preliminary Extraction:** Pulling out raw data elements such as dates, titles, and links for subsequent processing.

**How We Are Doing It:**  
- **Implementation:**  
  - **Scraping:** Using libraries like *BeautifulSoup* (or Scrapy for more complex cases).  
  - **PDF Parsing:** Leveraging libraries such as *pdfminer.six* or *PyPDF2* to convert PDFs into text.  
  - **Task Scheduling:** Utilizing Celery (or Django Q) to run periodic scraping/parsing tasks.
  - **Error Handling:** Implement logging and alerts for failed scraping or parsing tasks.

**Integration:**  
- Outputs from this feature feed directly into the AI processing pipeline within the **Data_Engine** app for further enrichment.

**Data Storage (in `data_engine/models.py`):**  
- **WebsiteConfig**  
  - *Fields:* `id`, `url`, `scraping_frequency`, `last_scrape_date`, `auth_info` (if needed).  
- **ScrapeTaskLog**  
  - *Fields:* `id`, `website` (ForeignKey to WebsiteConfig), `status` (e.g., success/failure), `timestamp`, `error_message` (optional).  
- **RawNotification**  
  - *Fields:* `id`, `website` (ForeignKey), `content` (raw text/HTML), `document_type` (choices: 'html', 'pdf'), `scraped_date`.

**Alternatives:**  
- If scaling is an issue, consider a cloud-based scraping service.
- For very large or complex scraping needs, migrate to a framework like Scrapy.

---

## **Feature 2: AI‑Based Chat Interface**

**Objective:**  
Provide an interactive natural language interface so users can ask detailed queries (e.g., “What was the last exam registration deadline?”) and receive clear, context-aware answers.

**What We Are Doing:**  
- **Query Interpretation:** Employ NLP techniques to parse user queries and extract key intents and entities (e.g., exam names, dates, event types).  
- **Response Generation:** Map the parsed query to structured notification data and generate human-friendly responses.  
- **Session Management:** Support multi-turn conversations to handle follow‑up queries.

**How We Are Doing It:**  
- **Implementation:**  
  - **Chatbot Engine:** Develop or integrate an NLP chatbot using frameworks like *Rasa* or *Dialogflow* or a custom solution using pre‑trained transformer models (e.g., from HuggingFace).  
  - **API Endpoints:** Expose RESTful APIs for chat query processing and response retrieval.  
  - **Context Management:** Maintain chat sessions to ensure coherent multi‑turn dialogues.

**Integration:**  
- This interface lives in the **Data_Engine** app and leverages enriched notification data from Feature 1 (after processing) to answer queries.
- It can also consider user preferences (from Feature 4) to tailor responses.

**Data Storage (in `data_engine/models.py`):**  
- **ChatSession**  
  - *Fields:* `id`, `user` (ForeignKey to Core’s User, if applicable), `start_time`, `last_interaction`.  
- **ChatMessage**  
  - *Fields:* `id`, `session` (ForeignKey to ChatSession), `sender` (choices: 'user' or 'system'), `message_text`, `timestamp`.

**Alternatives:**  
- Outsource to a third‑party chatbot service if in‑house development is too resource‑intensive.
- Use pre‑trained conversational models with fine‑tuning on domain-specific data.

---

## **Feature 3: Personalized Notification and Alert System**

**Objective:**  
Automatically deliver timely, targeted notifications to users about key events (e.g., exam registration deadlines) using multiple channels.

**What We Are Doing:**  
- **Alert Triggering:** Continuously monitor processed notifications for events that meet user‑defined triggers (e.g., approaching deadlines).  
- **Multi‑Channel Delivery:** Send alerts via email, SMS, and in‑app messages according to user preferences.  
- **Delivery Tracking:** Log each notification’s dispatch and status for performance monitoring.

**How We Are Doing It:**  
- **Implementation:**  
  - **Scheduling:** Use Celery to run background tasks that check for trigger events and queue notifications.  
  - **Delivery Integration:** Integrate with email services (e.g., SMTP, SendGrid) and SMS providers (e.g., Twilio).  
  - **Notification Rules:** Develop logic to match enriched data (from Feature 2) with user-defined criteria.

**Integration:**  
- This feature is housed in the **Notifier** app.  
- It pulls data from the **Data_Engine** (processed/enriched notifications) and applies user preference rules (from Feature 4).

**Data Storage (in `notifier/models.py`):**  
- **Notification**  
  - *Fields:* `id`, `user` (ForeignKey to Core’s User), `content`, `send_time`, `delivery_channel` (choices: 'email', 'sms', 'in-app'), `status` (e.g., 'pending', 'sent', 'failed').  
- **NotificationHistory** (optional)  
  - *Fields:* `id`, `notification` (ForeignKey), `delivery_time`, `result` (success, error message).

**Alternatives:**  
- For real‑time alerting, consider using Django Channels.
- Leverage third‑party notification platforms if managing multi‑channel delivery in‑house becomes too complex.

---

## **Feature 4: User Personalization & Preference Management**

**Objective:**  
Allow users to customize their experience by defining preferences and interests, ensuring that notifications and chat responses are tailored specifically to their needs.

**What We Are Doing:**  
- **Preference Configuration:** Enable users to select the types of notifications they want (e.g., specific exams, registration updates) and choose their preferred delivery channels and frequency.  
- **Content Filtering:** Use these preferences to filter enriched notifications and influence chatbot responses.  
- **Subscription Mapping:** Internally map users to relevant categories/topics for more accurate alert generation.

**How We Are Doing It:**  
- **Implementation:**  
  - **User Dashboard:** Create Django forms and views where users can set and update their preferences.  
  - **Data-Driven Rules:** Develop backend logic to filter and prioritize content based on stored user preferences.
  - **Feedback Loop:** Optionally, capture engagement data (e.g., which notifications are opened) to refine personalization over time.

**Integration:**  
- Implemented in the **Notifier** app (with ties to Core’s user management).  
- Directly influences both the Notification system (Feature 3) and the AI Chat interface (Feature 2).

**Data Storage (in `notifier/models.py`):**  
- **UserPreference**  
  - *Fields:* `id`, `user` (ForeignKey to Core’s User), `preferred_topics` (JSONField or many‑to‑many to a Topic model), `notification_channel`, `frequency` (e.g., immediate, daily, weekly).  
- **UserSubscription** (if maintained separately)  
  - *Fields:* `id`, `user` (ForeignKey), `category` (e.g., exam type), `is_active` (Boolean).

**Alternatives:**  
- Consider integrating a recommendation engine for dynamic preference adjustment if needed.
- Use external analytics to enhance personalization over time.

---

## **Summary & App Mapping**

- **Core App:**  
  - Provides global configuration and user/account management.
  - User model used by `UserPreference`, `ChatSession`, and `Notification`.

- **Data_Engine App:**  
  - **Feature 1:** Multi‑Source Data Aggregation and Parsing  
    - Models: `WebsiteConfig`, `ScrapeTaskLog`, `RawNotification`.
  - **Feature 2:** AI‑Based Chat Interface  
    - Models: `ChatSession`, `ChatMessage`.

- **Notifier App:**  
  - **Feature 3:** Personalized Notification and Alert System  
    - Models: `Notification`, `NotificationHistory`.
  - **Feature 4:** User Personalization & Preference Management  
    - Models: `UserPreference`, `UserSubscription`.