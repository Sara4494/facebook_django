
# Facebook Automation API Documentation

## Base URL
`https://facebook445.pythonanywhere.com/`

---

## Endpoints

### 1. Get Countries
**Endpoint:** `/api/countries/`  
**Method:** `GET`  
**Description:** Get distinct list of available countries.  

**Response Example:**
```json
{
  "countries": ["Egypt", "USA", "UK"]
}
```

---

### 2. Perform Facebook Action
**Endpoint:** `/api/facebook/action/`  
**Method:** `POST`  
**Description:** Perform an action (like, comment, etc.) on a post.  

**Request Body Example:**
```json
{
  "link": "https://facebook.com/post/123",
  "comment_text": "Nice post!",
  "country": "Egypt",
  "count": 2,
  "action": "comment"
}
```

**Response Example:**
```json
{
  "message": "Action \"comment\" started for 2 accounts in Egypt",
  "success": ["acc1@email.com", "acc2@email.com"],
  "failed": []
}
```

---

### 3. Publish Post (Text/Image)
**Endpoint:** `/api/facebook/post/`  
**Method:** `POST`  
**Description:** Publish a text or image post.  

**Request Body Example:**
```json
{
  "text": "Hello World!",
  "image_path": "/path/to/image.png",
  "country": "Egypt",
  "count": 3
}
```

**Response Example:**
```json
{
  "message": "Post publish attempt started for 3 accounts in Egypt"
}
```

---

### 4. Rate Facebook Page
**Endpoint:** `/api/facebook/rate/`  
**Method:** `POST`  
**Description:** Rate a Facebook page with review text.  

**Request Body Example:**
```json
{
  "link": "https://facebook.com/page/123",
  "review_text": "Great service!",
  "country": "Egypt",
  "count": 2
}
```

**Response Example:**
```json
{
  "message": "Rating page https://facebook.com/page/123 with Great service! stars started for 2 accounts",
  "success": ["acc1@email.com", "acc2@email.com"]
}
```

---

### 5. Save Facebook Account (Login)
**Endpoint:** `/api/facebook/login/`  
**Method:** `POST`  
**Description:** Save Facebook account credentials with optional cookie file.  

**Request Body Example:**
```json
{
  "email": "user@example.com",
  "password": "mypassword",
  "country": "Egypt",
  "cookie_file": "/tmp/cookie.json"
}
```

**Response Example:**
```json
{
  "message": "Account saved successfully",
  "account_id": 1,
  "created": true,
  "country": "Egypt",
  "cookie_file": "cookies/user@example.com_state.json"
}
```

---

### 6. Send Friend Requests
**Endpoint:** `/api/facebook/friend-requests/`  
**Method:** `POST`  
**Description:** Send friend requests by searching name.  

**Request Body Example:**
```json
{
  "search_name": "John Doe",
  "country": "Egypt",
  "count": 2,
  "max_requests_per_account": 5
}
```

**Response Example:**
```json
{
  "message": "Friend requests sending started for 2 accounts searching \"John Doe\" in Egypt"
}
```
