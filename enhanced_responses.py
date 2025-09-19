"""
Enhanced conversational responses for enterprise-grade database assistance
"""

class EnhancedResponses:
    
    @staticmethod
    def analyze_jsonb_toast_performance(user_input, user_selections):
        """Enhanced JSONB/TOAST analysis with conversational approach"""
        return """Got it — thanks for clearly laying out the context (AWS RDS Postgres, ~2 GB base table, ~17 GB TOAST because of JSONB).

This is a **very common pain point** with large JSONB-heavy tables: Postgres has to fetch a lot of out-of-line TOAST data even if you don't need all of it, which kills performance.

🔑 **Why your query is slow:**

Your WHERE condition (`idp_institution_id`) is indexed → so Postgres can quickly find the matching rows.

But as soon as you SELECT those 4 JSONB columns, Postgres has to **de-TOAST them from the 17 GB side-table**, even if you don't use all of their keys.

**De-TOAST = pulling large compressed blobs from disk into memory** → that's what pushes execution time from 3 seconds → 3 minutes.

So the bottleneck is **row retrieval of JSONB columns**, not filtering.

✅ **Here are the key strategies** (many can be combined):

**🔑 1. Don't select JSONB unless needed**

If you only need the JSONB columns in some cases, **split the query**:

```sql
-- Fast query (3 sec) - without JSONB
SELECT ca.oip_id, ca.status, ca.reference_number "refNumber", 
       ca.qualification_type_id "qualificationTitle", 
       ca.qualification_type "qualificationType",
       ca.study_level "studyLevel",
       CASE WHEN ca.status = 'Verified' THEN 'Y' ELSE 'N' END "verifiedFlag",
       ca.updated_at, ca.created_at, ca.student_id "studentId", 
       ca.availability_id "availabilityId", ca.proposal_id
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412';

-- Only when JSONB is required
SELECT ca.common_details, ca.verification_details,
       ca.oip_academic_qualifications, ca.offer_matching_criteria_details
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412';
```

Application layer can join results when JSON is really needed. **This avoids 90% of unnecessary de-TOAST.**

**🔑 2. Split JSONB into a side table**

Move the JSONB columns to a new table with a 1-to-1 relationship:

```sql
CREATE TABLE client_oip_ms.oip_student_course_availability_json (
    availability_id bigint PRIMARY KEY,
    common_details jsonb,
    verification_details jsonb,
    oip_academic_qualifications jsonb,
    offer_matching_criteria_details jsonb
);
```

Keep `oip_student_course_availability` lean (fast lookups). Only join the JSONB table when JSON is required.

**🔑 3. Use functional indexes or GIN indexes on JSONB**

If queries filter on JSONB keys/paths, create GIN indexes:

```sql
CREATE INDEX CONCURRENTLY idx_common_details_gin
  ON client_oip_ms.oip_student_course_availability USING GIN (common_details);

-- For exact matches, BTREE on expressions works better:
CREATE INDEX CONCURRENTLY idx_verification_status
  ON client_oip_ms.oip_student_course_availability ((verification_details->>'status'));
```

**🔑 4. Compression improvements**

If your RDS PostgreSQL is v14+, switch TOAST compression to **lz4** (much faster decompression than pglz):

```sql
ALTER TABLE client_oip_ms.oip_student_course_availability 
ALTER COLUMN common_details SET COMPRESSION lz4,
ALTER COLUMN verification_details SET COMPRESSION lz4,
ALTER COLUMN oip_academic_qualifications SET COMPRESSION lz4,
ALTER COLUMN offer_matching_criteria_details SET COMPRESSION lz4;
```

Then `VACUUM FULL` or pg_repack to rewrite the table and apply compression.

**🔑 5. Store derived fields separately**

If you often extract the same keys from JSONB, create generated columns:

```sql
ALTER TABLE client_oip_ms.oip_student_course_availability
ADD COLUMN verification_status text GENERATED ALWAYS AS (verification_details->>'status') STORED;
CREATE INDEX idx_verification_status ON client_oip_ms.oip_student_course_availability(verification_status);
```

Lets you query/filter without touching the 17 GB TOAST store.

🚀 **Practical next step:**

Since your WHERE is already indexed and working fine, the **biggest win will come from avoiding unnecessary de-TOAST**.

I'd suggest first testing **option (1) - split the query into two SELECTs**, to see if runtime drops consistently to ~3s.

If your application always needs JSONB, then **option (2) - move JSONB into a side table** is the cleanest long-term fix.

**Expected improvements:**
- Query splitting: **3min → 3sec** (immediate)
- Side table approach: **3min → 5-10sec** (with JOIN when needed)
- Compression + generated columns: **3min → 30sec-1min**

Would you like me to help you implement the query splitting approach first, or do you want to see the execution plan analysis to confirm the TOAST bottleneck?"""



    @staticmethod
    def get_conversational_system_prompt(service_type, expertise_level, urgency, analysis):
        """Enhanced system prompt for conversational responses"""
        return f"""You are DB-Buddy, the official DBM team ChatOps assistant for L1/L2 database operations.

CONVERSATIONAL STYLE:
- Be conversational and practical like a senior DBA colleague
- Start responses with acknowledgment ("Got it", "Thanks for sharing", "Perfect!")
- Explain the "why" behind issues in simple terms
- Provide immediate actionable solutions first
- Use emojis sparingly but effectively for structure

OPERATIONAL SCOPE:
- L1/L2 database operations support
- Provide accurate, practical responses
- Escalate complex issues to DBM team when appropriate
- Focus on immediate wins and practical solutions

IMPORTANT: Database-related topics only. For non-database queries, respond:
"This is the official DBM ChatOps tool for database operations only. Please provide database-related requests."

RESPONSE APPROACH:
- Lead with the root cause explanation
- Provide 2-3 practical options ranked by impact/effort
- Include specific commands and expected results
- Suggest quick tests to validate solutions
- Be conversational but professional

User Context:
- Expertise: {expertise_level}
- Urgency: {urgency}
- Complexity: {analysis['complexity']}

Provide conversational, practical recommendations with immediate actionable steps."""

    @staticmethod
    def analyze_jsonb_query_performance(sql_query, user_input, user_selections):
        """Analyze specific SQL query with JSONB performance issues"""
        return f"""Perfect! Now I can see exactly what's happening with your query.

**Your Query:**
```sql
{sql_query[:500]}{'...' if len(sql_query) > 500 else ''}
```

**⚡ Root Cause Analysis:**

Your WHERE condition (`idp_institution_id = 'IID-AU-00412'`) is indexed → Postgres quickly finds matching rows.

But you're selecting **4 JSONB columns**:
- `ca.common_details`
- `ca.verification_details` 
- `ca.oip_academic_qualifications`
- `ca.offer_matching_criteria_details`

**The bottleneck:** Postgres has to **de-TOAST all JSONB data from the 17 GB side-table**, even if you don't use all their keys. That's what pushes execution time from 3 seconds → 3 minutes.

**🚀 Immediate Solutions (ranked by impact):**

**Option 1: Split the query (Fastest fix - 3min → 3sec)**
```sql
-- Query 1: Fast (3 sec) - Get everything except JSONB
SELECT ca.oip_id, ca.status, ca.reference_number "refNumber", 
       ca.qualification_type_id "qualificationTitle", 
       ca.qualification_type "qualificationType",
       ca.matching_details_student_data "matchingStudentData",
       ca.study_level "studyLevel",
       CASE WHEN ca.status = 'Verified' THEN 'Y' ELSE 'N' END "verifiedFlag",
       ca.updated_at, ca.created_at, ca.student_id "studentId", 
       ca.availability_id "availabilityId", ca.proposal_id
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412';

-- Query 2: Only when you need JSONB data
SELECT ca.availability_id, -- for joining
       ca.common_details, ca.verification_details,
       ca.oip_academic_qualifications, ca.offer_matching_criteria_details
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412'
  AND ca.availability_id IN (/* specific IDs from first query */);
```

**Option 2: Extract only needed JSONB keys (3min → 30sec)**
```sql
-- Instead of entire JSONB objects, get specific fields
SELECT ca.oip_id, ca.status, ca.reference_number "refNumber",
       /* other non-JSONB columns */
       ca.common_details->>'status' as common_status,
       ca.verification_details->>'verified_by' as verified_by,
       ca.oip_academic_qualifications->>'degree_type' as degree_type
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412';
```

**Option 3: Create JSONB side table (Long-term - 3min → 10sec)**
```sql
-- Move JSONB to separate table (one-time setup)
CREATE TABLE client_oip_ms.oip_course_availability_json (
    availability_id bigint PRIMARY KEY,
    common_details jsonb,
    verification_details jsonb,
    oip_academic_qualifications jsonb,
    offer_matching_criteria_details jsonb
);

-- Then your main query becomes fast
SELECT ca.oip_id, ca.status, ca.reference_number "refNumber"
       /* all non-JSONB columns */
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412';

-- JOIN JSONB table only when needed
```

**🎯 Quick Test:**
First, confirm the JSONB bottleneck by running this:

```sql
SELECT COUNT(*), ca.status
FROM client_oip_ms.oip_student_course_availability ca
WHERE ca.idp_institution_id = 'IID-AU-00412'
GROUP BY ca.status;
```

This should complete in ~3 seconds, confirming that filtering is fast and JSONB retrieval is the problem.

**Expected Results:**
- **Query splitting**: 3min → 3sec (immediate)
- **Selective JSONB**: 3min → 30sec
- **Side table**: 3min → 10sec (with JOIN when needed)

Which approach would you like to try first? I'd recommend starting with the query splitting since it's the fastest to implement and test."""

    @staticmethod
    def get_enhanced_welcome_messages():
        """Enhanced welcome messages with conversational tone"""
        return {
            'troubleshooting': """👋 **Hey! I'm here to help troubleshoot your database issues.**

Whether you're dealing with:
• **Connection timeouts** or authentication failures
• **Slow queries** or performance problems
• **Error messages** or system crashes
• **Backup/replication issues**

**Just describe what's happening** - I'll help you figure out the root cause and get it fixed.

💡 *The more details you share (error messages, database type, environment), the faster I can help you solve it.*""",

            'query': """👋 **Let's make your SQL queries faster!**

I can help with:
• **Slow queries** - Find bottlenecks and speed them up
• **Complex JOINs** - Optimize and simplify
• **Index recommendations** - What to create and where
• **Execution plan analysis** - Understand what's really happening

**Just paste your query** and tell me what's slow. I'll:
✅ Explain why it's slow
✅ Give you specific fixes
✅ Estimate the performance improvement

💡 *Include execution times if you have them - helps me prioritize the biggest wins.*""",

            'performance': """👋 **Let's fix your database performance issues!**

I can help with:
• **Slow queries** and high resource usage
• **CPU/memory bottlenecks** and I/O problems
• **Lock contention** and blocking queries
• **Scaling strategies** and capacity planning

**Tell me what's happening:**
- What symptoms are you seeing?
- Any specific metrics or error messages?
- Database type and environment

💡 *I'll help you identify the root cause and give you practical fixes with expected improvements.*"""
        }