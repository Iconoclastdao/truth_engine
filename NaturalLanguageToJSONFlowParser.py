# Copyright (c) 2024 Your Name
#
# This software is dual-licensed:
#
# - For individuals and non-commercial use: Licensed under the MIT License.
# - For commercial or corporate use: A separate commercial license is required.
#
# To obtain a commercial license, please contact: iconoclastdao@gmail.com
#
# By using this software, you agree to these terms.
#
# MIT License (for individuals and non-commercial use):
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import spacy
import json
import uuid
from typing import Dict, List, Any
import re

# Check if en_core_web_sm is installed, download if not
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class JSONFlowParser:
    def __init__(self):
        self.schema = {
            "function": "",
            "schema": {
                "inputs": {},
                "context": {}
            },
            "context": {},
            "steps": []
        }
        self.variable_types = ["string", "int", "dict", "array", "bool"]
        self.step_templates = {
            "set": {
                "set": {
                    "target": "",
                    "value": ""
                }
            },
            "assert": {
                "assert": {
                    "condition": {
                        "compare": {
                            "left": "",
                            "op": "",
                            "right": ""
                        }
                    },
                    "message": ""
                }
            },
            "log": {
                "log": {
                    "level": "info",
                    "message": []
                }
            },
            "forEach": {
                "forEach": {
                    "source": "",
                    "as": "",
                    "body": []
                }
            }
        }
        self.comparison_ops = ["==", "!=", ">", "<", ">=", "<=", "in"]

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into a JSONFlow schema."""
        doc = nlp(text)
        self.schema["function"] = self._generate_function_name(doc)
        self._process_sentences(doc)
        return self.schema

    def _generate_function_name(self, doc) -> str:
        """Generate a function name from the text."""
        for sent in doc.sents:
            for token in sent:
                if token.pos_ == "VERB" and token.lemma_ in ["create", "build", "define", "generate"]:
                    return f"{token.text.capitalize()}Workflow"
        return "DefaultWorkflow"

    def _process_sentences(self, doc):
        """Process each sentence to extract JSONFlow components."""
        current_step = None
        for sent in doc.sents:
            if "input" in sent.text.lower():
                self._parse_input(sent)
            elif "set" in sent.text.lower() or "assign" in sent.text.lower():
                current_step = self._parse_set_step(sent)
                if current_step:
                    self.schema["steps"].append(current_step)
            elif "if" in sent.text.lower() or "check" in sent.text.lower():
                current_step = self._parse_assert_step(sent)
                if current_step:
                    self.schema["steps"].append(current_step)
            elif "log" in sent.text.lower() or "print" in sent.text.lower():
                current_step = self._parse_log_step(sent)
                if current_step:
                    self.schema["steps"].append(current_step)
            elif "for each" in sent.text.lower() or "loop" in sent.text.lower():
                current_step = self._parse_foreach_step(sent)
                if current_step:
                    self.schema["steps"].append(current_step)
            elif "context" in sent.text.lower() or "variable" in sent.text.lower():
                self._parse_context(sent)

    def _parse_input(self, sent):
        """Parse sentences describing inputs."""
        doc = nlp(sent.text)
        input_name = None
        input_type = "string"
        description = ""

        for token in doc:
            if token.text.lower() == "input" and token.head.pos_ == "NOUN":
                input_name = token.head.text
            elif token.text.lower() in self.variable_types:
                input_type = token.text.lower()
            elif token.dep_ == "attr" or token.dep_ == "dobj":
                description = token.text

        if input_name:
            self.schema["schema"]["inputs"][input_name] = {
                "type": input_type,
                "description": description or f"Input {input_name}"
            }

    def _parse_context(self, sent):
        """Parse sentences describing context variables."""
        doc = nlp(sent.text)
        var_name = None
        var_type = "string"

        for token in doc:
            if token.text.lower() in ["variable", "context"] and token.head.pos_ == "NOUN":
                var_name = token.head.text
            elif token.text.lower() in self.variable_types:
                var_type = token.text.lower()

        if var_name:
            self.schema["schema"]["context"][var_name] = var_type
            self.schema["context"][var_name] = "" if var_type == "string" else [] if var_type == "array" else {}

    def _parse_set_step(self, sent) -> Dict[str, Any]:
        """Parse sentences describing a set operation."""
        doc = nlp(sent.text)
        target = None
        value = None

        for token in doc:
            if token.text.lower() in ["set", "assign"] and token.head.pos_ == "NOUN":
                target = token.head.text
            elif token.dep_ == "attr" or token.dep_ == "dobj":
                value = token.text

        if target and value:
            step = self.step_templates["set"].copy()
            step["set"]["target"] = target
            step["set"]["value"] = {"get": value} if value in self.schema["schema"]["inputs"] else value
            return step
        return None

    def _parse_assert_step(self, sent) -> Dict[str, Any]:
        """Parse sentences describing a condition check."""
        doc = nlp(sent.text)
        condition = None
        left = None
        op = None
        right = None
        message = "Condition failed"

        # Extract condition components
        for token in doc:
            if token.text.lower() in ["if", "check"]:
                condition = token.head.text
            elif token.dep_ == "nsubj" and token.head.text == condition:
                left = token.text
            elif token.text in self.comparison_ops:
                op = token.text
            elif token.dep_ == "attr" or token.dep_ == "dobj":
                right = token.text

        if left and op and right:
            step = self.step_templates["assert"].copy()
            step["assert"]["condition"]["compare"]["left"] = {"get": left} if left in self.schema["schema"]["inputs"] else left
            step["assert"]["condition"]["compare"]["op"] = op
            step["assert"]["condition"]["compare"]["right"] = {"get": right} if right in self.schema["schema"]["inputs"] else right
            step["assert"]["message"] = f"{left} {op} {right} check failed"
            return step
        return None

    def _parse_log_step(self, sent) -> Dict[str, Any]:
        """Parse sentences describing a log operation."""
        doc = nlp(sent.text)
        message_parts = []

        for token in doc:
            if token.dep_ in ["nsubj", "dobj", "attr"]:
                message_parts.append(token.text)

        if message_parts:
            step = self.step_templates["log"].copy()
            step["log"]["message"] = [
                {"get": part} if part in self.schema["schema"]["inputs"] else part
                for part in message_parts
            ]
            return step
        return None

    def _parse_foreach_step(self, sent) -> Dict[str, Any]:
        """Parse sentences describing a loop operation."""
        doc = nlp(sent.text)
        source = None
        iterator = None

        for token in doc:
            if token.text.lower() in ["each", "loop"] and token.head.pos_ == "NOUN":
                source = token.head.text
            elif token.dep_ == "nsubj" and token.head.text.lower() in ["each", "loop"]:
                iterator = token.text

        if source and iterator:
            step = self.step_templates["forEach"].copy()
            step["forEach"]["source"] = source
            step["forEach"]["as"] = iterator
            step["forEach"]["body"] = []  # Body can be populated by subsequent sentences
            return step
        return None

def generate_jsonflow_from_text(text: str) -> Dict[str, Any]:
    """Generate a JSONFlow schema from natural language text."""
    parser = JSONFlowParser()
    schema = parser.parse(text)
    return {
        "artifact_id": str(uuid.uuid4()),
        "title": "GeneratedJSONFlowSchema.json",
        "contentType": "application/json",
        "schema": schema
    }

def main():
    # Example natural language input
    sample_text = """
    Create a workflow to process user data.
    Take an input called username as a string.
    Take an input called age as an integer.
    Define a context variable called result as a string.
    Set result to username.
    If age is greater than 18, log the message "User is adult".
    For each item in permissions, log the item.
    """
    
    result = generate_jsonflow_from_text(sample_text)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()