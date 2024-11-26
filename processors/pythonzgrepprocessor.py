import subprocess
import io
import gzip

from nifiapi.flowfiletransform import FlowFileTransform, FlowFileTransformResult
from nifiapi.properties import PropertyDescriptor, StandardValidators

ZGREP_COMMAND = "zgrep"
RG_COMMAND = "rg"

class PythonZgrepProcessor(FlowFileTransform):
    class Java:
        implements = ['org.apache.nifi.python.processor.FlowFileTransform']
    class ProcessorDetails:
        version = '1.0.0'
        description = """Parses incoming zip file and runs a grep on the file with passed arguments, the output of zgrep command is returned in a flowfile as content."""
        tags = ["zip", "gz", "zgrep", "grep", "rg", "python", "re"]

    def __init__(self, jvm=None, **kwargs):
        self.jvm = jvm

        self.GREP_COMMAND_TO_USE = PropertyDescriptor(
            name="System grep command to be used",
            description="""Specifies which grep command is to be used. rg has better performance. Note: rg grep should be installed on system if used""",
            allowable_values=[ZGREP_COMMAND, RG_COMMAND],
            required=True,
            default_value=ZGREP_COMMAND
        )

        self.IGNORE_ZERO_BYTE_OUTPUT = PropertyDescriptor(
            name="Ignore Zero Byte Output",
            description="""Specifies if there is no match for the passed regex, a zero byter flowfile should be created or not""",
            allowable_values=["Yes", "No"],
            required=True,
            default_value="Yes"
        )

        self.INPUT_STRING_OR_REGEX = PropertyDescriptor(
            name="String or Regex to match",
            description="""Specifies the string or regex to match on the input flowfiles""",
            required=True,
            validators=[StandardValidators.NON_EMPTY_VALIDATOR]
        )

        self.property_descriptors = [self.GREP_COMMAND_TO_USE, self.IGNORE_ZERO_BYTE_OUTPUT, self.INPUT_STRING_OR_REGEX]

    def onScheduled(self, context):
        self.grep_command = context.getProperty(self.GREP_COMMAND_TO_USE).getValue()
        self.search_regex = context.getProperty(self.INPUT_STRING_OR_REGEX).getValue()

    def getPropertyDescriptors(self):
        return self.property_descriptors

    def transform(self, context, flowFile):
        try:
            process = subprocess.Popen([self.grep_command, self.search_regex, '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            compressed_file_object = io.BytesIO(flowFile.getContentsAsBytes())
            output, errors = process.communicate(input=compressed_file_object.read())
            output = gzip.compress(output)

            if output:
                return FlowFileTransformResult(relationship = "success", contents = output)
            else:
                return FlowFileTransformResult(relationship = "original")
        except Exception as e:
            self.logger.error(e)
            return FlowFileTransformResult(relationship = "failure")