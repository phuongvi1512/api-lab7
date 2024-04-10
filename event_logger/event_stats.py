from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class EventStats(Base):

    __tablename__ = "event_stats"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(250), nullable=False)
    message_code = Column(String(250), nullable=False)
    message = Column(String(250), nullable=False)
    last_updated = Column(DateTime, nullable=False)

    def __init__(self, trace_id, message_code, message):
        """  """
        self.trace_id = trace_id
        self.message_code = message_code
        self.message = message
        self.last_updated = datetime.datetime.now() # Sets the date/time record is created

    def to_dict(self):
        """ Dictionary Representation of a heart rate reading """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['message_code'] = self.message_code
        dict['message'] = self.message
        dict['last_updated'] = self.last_updated

        return dict
