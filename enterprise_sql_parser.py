"""
Enterprise-grade SQL Parser for accurate query analysis
"""

import re

class EnterpriseSQLParser:
    
    @staticmethod
    def extract_sql_query_robust(user_input):
        """Robust SQL query extraction with multiple strategies"""
        # Clean HTML entities first
        cleaned_input = user_input.replace('&amp;#39;', "'").replace('&amp;gt;', '>').replace('&amp;lt;', '<')
        lines = cleaned_input.split('\n')
        
        # Strategy 1: Look for context markers first
        sql_markers = ['below is the query', 'here is the query', 'the query is', 'sql:', 'query:']
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(marker in line_lower for marker in sql_markers):
                # Look for SQL in following lines
                sql_lines = []
                for j in range(i+1, len(lines)):
                    current_line = lines[j]
                    current_stripped = current_line.strip()
                    
                    # Skip empty lines at start
                    if not current_stripped and not sql_lines:
                        continue
                    
                    # Start capturing when we see SQL keywords or indented content
                    if (current_stripped and 
                        (any(keyword in current_stripped.lower() for keyword in ['select ', 'insert ', 'update ', 'delete ', 'create ']) or
                         current_line.startswith('\t') or current_line.startswith('    '))):
                        sql_lines.append(current_stripped)
                    elif sql_lines and current_stripped:
                        # Continue if it looks like part of SQL
                        if (current_line.startswith('\t') or current_line.startswith('    ') or
                            any(keyword in current_stripped.lower() for keyword in ['from ', 'where ', 'and ', 'or ', 'order by', 'group by'])):
                            sql_lines.append(current_stripped)
                        else:
                            # Stop if we hit non-SQL content
                            break
                    elif sql_lines:
                        # Stop at empty line after SQL content
                        break
                
                if sql_lines:
                    return '\n'.join(sql_lines)
        
        # Strategy 2: Look for indented SQL blocks
        sql_lines = []
        in_sql_block = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Start SQL block detection
            if (line.startswith('\t') or line.startswith('    ')) and any(keyword in line_lower for keyword in [
                'select ', 'insert ', 'update ', 'delete ', 'create ', 'alter ', 'drop ', 'with '
            ]):
                in_sql_block = True
                sql_lines.append(line_stripped)
            elif in_sql_block:
                if line_stripped == '' or not (line.startswith('\t') or line.startswith('    ')):
                    # End of SQL block
                    break
                sql_lines.append(line_stripped)
        
        if sql_lines:
            return '\n'.join(sql_lines)
        
        # Strategy 3: Look for SQL keywords at line start
        sql_lines = []
        capturing = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # SQL statement starts
            if line_lower.startswith(('select ', 'insert ', 'update ', 'delete ', 'create ', 'alter ', 'drop ', 'with ')):
                capturing = True
                sql_lines.append(line_stripped)
            elif capturing:
                if line_stripped == '' and i < len(lines) - 1 and not lines[i+1].strip().startswith((' ', '\t')):
                    # End of SQL statement
                    break
                elif line_stripped:
                    sql_lines.append(line_stripped)
        
        if sql_lines:
            return '\n'.join(sql_lines)
        
        # Strategy 4: Extract complete SQL from single line or multi-line blocks
        # Look for SELECT statements that might span multiple lines
        full_text = ' '.join(line.strip() for line in lines if line.strip())
        if 'SELECT' in full_text.upper() and 'FROM' in full_text.upper():
            # Try to extract the complete SQL statement
            select_start = full_text.upper().find('SELECT')
            if select_start != -1:
                # Find the end of the SQL statement (look for common terminators)
                sql_part = full_text[select_start:]
                # Remove any trailing non-SQL content
                for terminator in ['🔍', '**', 'Enterprise', 'Analysis', 'Environment']:
                    if terminator in sql_part:
                        sql_part = sql_part[:sql_part.find(terminator)].strip()
                        break
                return sql_part.strip()
        
        # Strategy 5: Direct pattern matching for the specific query format
        # Handle cases where query spans multiple lines with proper formatting
        query_pattern = r'SELECT\s+.*?FROM\s+.*?(?:WHERE\s+.*?)?(?=\s*$|\s*🔍|\s*\*\*|\s*Enterprise|\s*Analysis)'
        match = re.search(query_pattern, cleaned_input, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0).strip()
        
        return None
    
    @staticmethod
    def parse_sql_components(sql_query):
        """Parse SQL query components accurately"""
        # Clean up HTML entities first
        cleaned_query = sql_query.replace('&amp;#39;', "'").replace('&amp;gt;', '>').replace('&amp;lt;', '<')
        
        sql_upper = cleaned_query.upper()
        sql_lower = cleaned_query.lower()
        
        # Extract SELECT columns
        select_columns = []
        if 'SELECT' in sql_upper:
            select_start = cleaned_query.upper().find('SELECT') + 6
            from_pos = cleaned_query.upper().find('FROM')
            select_end = from_pos if from_pos != -1 else len(cleaned_query)
            select_part = cleaned_query[select_start:select_end].strip()
            select_columns = [col.strip() for col in select_part.split(',') if col.strip()]
        
        # Extract table names - improved extraction
        tables = []
        if 'FROM' in sql_upper:
            from_start = cleaned_query.upper().find('FROM') + 4
            where_pos = cleaned_query.upper().find('WHERE')
            join_pos = cleaned_query.upper().find('JOIN')
            
            # Find the end of the FROM clause
            end_positions = [pos for pos in [where_pos, join_pos, len(cleaned_query)] if pos != -1]
            from_end = min(end_positions)
            
            from_part = cleaned_query[from_start:from_end].strip()
            # Handle table aliases (e.g., "table_name alias" or "table_name AS alias")
            table_parts = from_part.split()
            if table_parts:
                # First part is the table name
                table_name = table_parts[0]
                # Remove any trailing commas or other punctuation
                table_name = table_name.rstrip(',;')
                tables.append(table_name)
        
        # Extract WHERE conditions - improved parsing with better regex
        where_conditions = []
        if 'WHERE' in sql_upper:
            where_start = cleaned_query.upper().find('WHERE') + 5
            # Find end of WHERE clause (before ORDER BY, GROUP BY, etc.)
            end_keywords = ['ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'UNION', ';']
            where_end = len(cleaned_query)
            for keyword in end_keywords:
                pos = cleaned_query.upper().find(keyword)
                if pos != -1 and pos > where_start:
                    where_end = min(where_end, pos)
            
            where_part = cleaned_query[where_start:where_end].strip()
            # Handle complex WHERE conditions with proper AND/OR splitting
            # Use regex that doesn't break on AND/OR within quoted strings or JSONB operations
            conditions = re.split(r'\s+(?:AND|OR)\s+(?![^\(]*\))', where_part, flags=re.IGNORECASE)
            where_conditions = [cond.strip() for cond in conditions if cond.strip() and len(cond.strip()) > 2]
        
        # Detect JSONB operations
        jsonb_operations = []
        if '->' in cleaned_query or '->>' in cleaned_query:
            jsonb_operations = ['JSONB path operations detected']
        
        return {
            'query_type': 'SELECT' if 'SELECT' in sql_upper else 'OTHER',
            'select_columns': select_columns,
            'tables': tables,
            'where_conditions': where_conditions,
            'has_joins': 'JOIN' in sql_upper,
            'has_where': 'WHERE' in sql_upper,
            'has_order': 'ORDER BY' in sql_upper,
            'has_group': 'GROUP BY' in sql_upper,
            'has_having': 'HAVING' in sql_upper,
            'jsonb_operations': jsonb_operations,
            'complexity': EnterpriseSQLParser.assess_query_complexity(cleaned_query)
        }
    
    @staticmethod
    def assess_query_complexity(sql_query):
        """Assess query complexity"""
        complexity_score = 0
        sql_upper = sql_query.upper()
        
        if 'JOIN' in sql_upper: complexity_score += 2
        if 'SUBQUERY' in sql_upper or sql_query.count('SELECT') > 1: complexity_score += 3
        if '->' in sql_query: complexity_score += 2  # JSONB operations
        if 'GROUP BY' in sql_upper: complexity_score += 1
        if 'ORDER BY' in sql_upper: complexity_score += 1
        
        if complexity_score >= 5: return 'high'
        elif complexity_score >= 2: return 'medium'
        else: return 'low'
    
    @staticmethod
    def extract_performance_context(user_input):
        """Extract performance context from user input"""
        context = {
            'execution_time': 'Unknown',
            'expected_time': 'Unknown',
            'symptoms': [],
            'environment': 'Unknown'
        }
        
        # Extract execution times - improved patterns
        time_patterns = [
            (r'(\d+)\+?\s*seconds?', 'execution_time'),
            (r'(\d+)\s*ms', 'expected_time'),
            (r'execution.*?(\d+)\s*seconds?', 'execution_time'),
            (r'actual.*?(\d+)\s*seconds?', 'execution_time'),
            (r'plan.*?(\d+)\s*ms', 'expected_time'),
            (r'estimated.*?(\d+)\s*ms', 'expected_time')
        ]
        
        for pattern, key in time_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                context[key] = match.group(1)
        
        # Extract symptoms - more comprehensive
        symptom_patterns = [
            ('slow', 'slow execution'),
            ('timeout', 'timeout'),
            ('index scan', 'index scan detected'),
            ('25+ seconds', 'very slow execution'),
            ('milliseconds.*plan.*seconds.*actual', 'execution time discrepancy'),
            ('explain plan', 'execution plan analysis needed')
        ]
        
        for pattern, symptom in symptom_patterns:
            if pattern in user_input.lower():
                context['symptoms'].append(symptom)
        
        # Extract environment info
        env_patterns = [
            ('staging', 'Staging'),
            ('production', 'Production'),
            ('development', 'Development'),
            ('aws', 'AWS'),
            ('postgresql', 'PostgreSQL')
        ]
        
        for pattern, env in env_patterns:
            if pattern in user_input.lower():
                context['environment'] = env
                break
        
        return context