from datetime import datetime
from . import db


class Search(db.Model):
    """A search session tracking query and results."""
    
    __tablename__ = 'searches'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    owner_filter = db.Column(db.String(255), nullable=True)
    language_filter = db.Column(db.String(50), nullable=True)
    pattern_kinds = db.Column(db.JSON, nullable=False)  # List of enabled patterns
    max_results = db.Column(db.Integer, default=20)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, running, completed, failed
    
    user_identifier = db.Column(db.String(255), nullable=True)  # For multi-user setups
    
    # Relationships
    # TODO: Add relationship when Result model is created
    # results = db.relationship('Result', back_populates='search', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Search {self.id}: {self.query[:50]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'owner_filter': self.owner_filter,
            'language_filter': self.language_filter,
            'pattern_kinds': self.pattern_kinds,
            'max_results': self.max_results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            # TODO: Add results_count when Result model is created
            # 'results_count': len(self.results) if self.results else 0,
        }
