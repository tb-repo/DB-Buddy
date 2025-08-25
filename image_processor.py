import base64
import io
from PIL import Image
import pytesseract
import requests
import os

class ImageProcessor:
    def __init__(self):
        # Set tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def process_image(self, image_data, image_type='base64'):
        """Process image and extract text content"""
        try:
            # Convert image data to PIL Image
            if image_type == 'base64':
                image = self.base64_to_image(image_data)
            elif image_type == 'file':
                image = Image.open(image_data)
            else:
                return None
            
            # Extract text using OCR
            extracted_text = self.extract_text_ocr(image)
            
            # Analyze image content
            analysis = self.analyze_image_content(extracted_text, image)
            
            return {
                'extracted_text': extracted_text,
                'analysis': analysis,
                'image_type': self.detect_image_type(extracted_text)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to process image: {str(e)}",
                'extracted_text': '',
                'analysis': '',
                'image_type': 'unknown'
            }
    
    def base64_to_image(self, base64_string):
        """Convert base64 string to PIL Image"""
        # Remove data URL prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        return image
    
    def extract_text_ocr(self, image):
        """Extract text from image using OCR"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use pytesseract to extract text
            extracted_text = pytesseract.image_to_string(image, config='--psm 6')
            return extracted_text.strip()
            
        except Exception as e:
            return f"OCR extraction failed: {str(e)}"
    
    def detect_image_type(self, text):
        """Detect what type of database-related content the image contains"""
        text_lower = text.lower()
        
        # SQL Query detection
        if any(keyword in text_lower for keyword in ['select', 'from', 'where', 'join', 'insert', 'update', 'delete']):
            return 'sql_query'
        
        # Execution plan detection
        if any(keyword in text_lower for keyword in ['execution time', 'cost', 'rows', 'hash join', 'seq scan', 'index scan']):
            return 'execution_plan'
        
        # Error message detection
        if any(keyword in text_lower for keyword in ['error', 'exception', 'failed', 'timeout', 'connection refused']):
            return 'error_message'
        
        # Performance metrics detection
        if any(keyword in text_lower for keyword in ['cpu', 'memory', 'disk', 'i/o', 'latency', 'throughput', '%']):
            return 'performance_metrics'
        
        # Database schema detection
        if any(keyword in text_lower for keyword in ['table', 'column', 'primary key', 'foreign key', 'index', 'constraint']):
            return 'database_schema'
        
        # Configuration detection
        if any(keyword in text_lower for keyword in ['config', 'parameter', 'setting', 'variable', 'my.cnf', 'postgresql.conf']):
            return 'configuration'
        
        return 'general_database'
    
    def analyze_image_content(self, text, image):
        """Analyze the extracted text and provide context"""
        image_type = self.detect_image_type(text)
        
        analysis = {
            'sql_query': self.analyze_sql_query,
            'execution_plan': self.analyze_execution_plan,
            'error_message': self.analyze_error_message,
            'performance_metrics': self.analyze_performance_metrics,
            'database_schema': self.analyze_database_schema,
            'configuration': self.analyze_configuration,
            'general_database': self.analyze_general
        }.get(image_type, self.analyze_general)(text)
        
        return analysis
    
    def analyze_sql_query(self, text):
        """Analyze SQL query from image"""
        return f"""
📸 **Image Analysis: SQL Query Detected**

**Extracted Query:**
```sql
{text}
```

**Initial Observations:**
- SQL query successfully extracted from image
- Ready for performance analysis and optimization recommendations
- Can provide indexing strategies and query rewrite suggestions

**Next Steps:**
- Share execution plan if available for detailed analysis
- Specify database system for targeted recommendations
- Describe performance issues you're experiencing
"""
    
    def analyze_execution_plan(self, text):
        """Analyze execution plan from image"""
        return f"""
📸 **Image Analysis: Execution Plan Detected**

**Extracted Plan:**
```
{text}
```

**Plan Analysis:**
- Execution plan successfully extracted from screenshot
- Can identify performance bottlenecks and optimization opportunities
- Ready to provide specific index recommendations

**Recommendations:**
- Will analyze costs, row estimates, and execution times
- Can suggest query optimizations and index strategies
- Provide expected performance improvements
"""
    
    def analyze_error_message(self, text):
        """Analyze error message from image"""
        return f"""
📸 **Image Analysis: Error Message Detected**

**Extracted Error:**
```
{text}
```

**Error Analysis:**
- Database error message successfully captured from image
- Can provide troubleshooting steps and root cause analysis
- Ready to suggest immediate fixes and preventive measures

**Next Steps:**
- Will provide specific troubleshooting steps
- Suggest configuration changes if needed
- Recommend monitoring and prevention strategies
"""
    
    def analyze_performance_metrics(self, text):
        """Analyze performance metrics from image"""
        return f"""
📸 **Image Analysis: Performance Metrics Detected**

**Extracted Metrics:**
```
{text}
```

**Performance Analysis:**
- System performance data successfully extracted from image
- Can identify resource bottlenecks and optimization opportunities
- Ready to provide tuning recommendations

**Optimization Areas:**
- Will analyze CPU, memory, and I/O patterns
- Suggest configuration optimizations
- Recommend monitoring and alerting strategies
"""
    
    def analyze_database_schema(self, text):
        """Analyze database schema from image"""
        return f"""
📸 **Image Analysis: Database Schema Detected**

**Extracted Schema:**
```
{text}
```

**Schema Analysis:**
- Database structure successfully extracted from image
- Can provide normalization and design recommendations
- Ready to suggest indexing and optimization strategies

**Design Review:**
- Will analyze table relationships and constraints
- Suggest performance optimizations
- Recommend best practices for schema design
"""
    
    def analyze_configuration(self, text):
        """Analyze configuration from image"""
        return f"""
📸 **Image Analysis: Configuration Detected**

**Extracted Configuration:**
```
{text}
```

**Configuration Analysis:**
- Database configuration successfully extracted from image
- Can review settings for optimization opportunities
- Ready to provide tuning recommendations

**Optimization Review:**
- Will analyze memory, connection, and performance settings
- Suggest environment-specific optimizations
- Recommend monitoring and maintenance configurations
"""
    
    def analyze_general(self, text):
        """Analyze general database content from image"""
        return f"""
📸 **Image Analysis: Database Content Detected**

**Extracted Content:**
```
{text}
```

**Content Analysis:**
- Database-related information successfully extracted from image
- Can provide relevant recommendations based on the content
- Ready to assist with your specific database needs

**Next Steps:**
- Please describe what specific help you need with this content
- Share additional context about your database environment
- Specify any performance or functionality concerns
"""
    
    def process_claude_vision(self, image_data, anthropic_api_key):
        """Use Claude Vision API for advanced image analysis"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=anthropic_api_key)
            
            # Convert image to base64 if needed
            if isinstance(image_data, str):
                image_base64 = image_data
            else:
                # Convert PIL image to base64
                buffer = io.BytesIO()
                image_data.save(buffer, format='PNG')
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": "Analyze this database-related image. Extract any SQL queries, execution plans, error messages, performance metrics, or configuration details. Provide specific recommendations for optimization or troubleshooting."
                            }
                        ]
                    }
                ]
            )
            
            return {
                'extracted_text': 'Analyzed by Claude Vision',
                'analysis': message.content[0].text,
                'image_type': 'claude_vision_analysis'
            }
            
        except Exception as e:
            return {
                'error': f"Claude Vision analysis failed: {str(e)}",
                'extracted_text': '',
                'analysis': '',
                'image_type': 'unknown'
            }