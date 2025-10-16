"""
Real-time collaboration engine for document editing and annotation.
Implements WebSocket-based real-time features with conflict resolution.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import threading

from ...database.models.base import Document, User
from ...core.errors.error_handler import handle_errors


@dataclass
class CollaborativeSession:
    """Real-time collaboration session."""
    session_id: str
    document_id: str
    participants: Dict[str, User] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    max_participants: int = 10
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentAnnotation:
    """Document annotation with real-time sync."""
    annotation_id: str
    document_id: str
    user_id: str
    annotation_type: str  # 'comment', 'highlight', 'note', 'suggestion'
    content: str
    position: Dict[str, Any]  # x, y, page, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborativeEdit:
    """Single collaborative edit operation."""
    edit_id: str
    session_id: str
    user_id: str
    operation_type: str  # 'insert', 'delete', 'replace', 'format'
    position: Dict[str, Any]
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    previous_version: Optional[int] = None


@dataclass
class DocumentVersion:
    """Document version for change tracking."""
    version_id: str
    document_id: str
    version_number: int
    content_snapshot: str
    changes: List[CollaborativeEdit]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    description: Optional[str] = None


class RealTimeEngine:
    """Main real-time collaboration engine."""

    def __init__(self):
        """Initialize real-time engine."""
        self.logger = logging.getLogger(__name__)

        # Active collaboration sessions
        self.active_sessions: Dict[str, CollaborativeSession] = {}

        # Document annotations
        self.document_annotations: Dict[str, List[DocumentAnnotation]] = defaultdict(list)

        # Document versions and history
        self.document_versions: Dict[str, List[DocumentVersion]] = defaultdict(list)

        # Connected clients (WebSocket connections)
        self.connected_clients: Dict[str, Dict[str, Any]] = {}

        # Operation queue for conflict resolution
        self.operation_queue: asyncio.Queue = asyncio.Queue()

        # Background task for processing operations
        self._processing_task: Optional[asyncio.Task] = None

        # Start background processing
        self._start_background_processing()

    def _start_background_processing(self) -> None:
        """Start background task for processing operations."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_operations())

    async def _process_operations(self) -> None:
        """Background task to process queued operations."""
        while True:
            try:
                # Get operation from queue
                operation = await self.operation_queue.get()

                # Process operation
                await self._handle_operation(operation)

                self.operation_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing operation: {e}")

    async def _handle_operation(self, operation: Dict[str, Any]) -> None:
        """Handle queued operation."""
        operation_type = operation.get('type')

        if operation_type == 'edit':
            await self._handle_collaborative_edit(operation)
        elif operation_type == 'annotation':
            await self._handle_annotation_update(operation)
        elif operation_type == 'cursor':
            await self._handle_cursor_update(operation)

    def create_collaboration_session(
        self,
        document_id: str,
        creator_user_id: str,
        max_participants: int = 10
    ) -> str:
        """Create new collaboration session.

        Args:
            document_id: Document to collaborate on
            creator_user_id: User creating the session
            max_participants: Maximum participants allowed

        Returns:
            Session ID
        """
        session_id = f"collab_{document_id}_{uuid.uuid4().hex[:8]}"

        session = CollaborativeSession(
            session_id=session_id,
            document_id=document_id,
            max_participants=max_participants,
            settings={
                'allow_anonymous': False,
                'require_approval': False,
                'auto_save': True,
                'conflict_resolution': 'last_write_wins'
            }
        )

        self.active_sessions[session_id] = session
        self.logger.info(f"Created collaboration session: {session_id}")

        return session_id

    def join_collaboration_session(
        self,
        session_id: str,
        user: User
    ) -> bool:
        """Join existing collaboration session.

        Args:
            session_id: Session to join
            user: User joining the session

        Returns:
            True if join successful
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        if not session.is_active:
            return False

        if len(session.participants) >= session.max_participants:
            return False

        if user.id in session.participants:
            return True  # Already joined

        session.participants[user.id] = user
        session.last_activity = datetime.utcnow()

        self.logger.info(f"User {user.username} joined session {session_id}")
        return True

    def leave_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """Leave collaboration session.

        Args:
            session_id: Session to leave
            user_id: User leaving

        Returns:
            True if leave successful
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        if user_id in session.participants:
            del session.participants[user_id]

            # End session if no participants left
            if not session.participants:
                session.is_active = False

            self.logger.info(f"User {user_id} left session {session_id}")
            return True

        return False

    def get_session_participants(self, session_id: str) -> List[User]:
        """Get participants in collaboration session.

        Args:
            session_id: Session ID

        Returns:
            List of participants
        """
        if session_id not in self.active_sessions:
            return []

        session = self.active_sessions[session_id]
        return list(session.participants.values())

    @handle_errors(operation="add_annotation", component="realtime_engine")
    def add_annotation(
        self,
        document_id: str,
        user_id: str,
        annotation_type: str,
        content: str,
        position: Dict[str, Any]
    ) -> str:
        """Add annotation to document.

        Args:
            document_id: Document to annotate
            user_id: User adding annotation
            annotation_type: Type of annotation
            content: Annotation content
            position: Position information

        Returns:
            Annotation ID
        """
        annotation_id = f"annotation_{uuid.uuid4().hex}"

        annotation = DocumentAnnotation(
            annotation_id=annotation_id,
            document_id=document_id,
            user_id=user_id,
            annotation_type=annotation_type,
            content=content,
            position=position
        )

        self.document_annotations[document_id].append(annotation)

        # Queue operation for real-time broadcast
        operation = {
            'type': 'annotation',
            'action': 'add',
            'annotation': annotation.__dict__,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Add to queue for async processing
        asyncio.create_task(self._broadcast_to_session(document_id, operation))

        self.logger.info(f"Added annotation {annotation_id} to document {document_id}")
        return annotation_id

    @handle_errors(operation="update_annotation", component="realtime_engine")
    def update_annotation(
        self,
        annotation_id: str,
        content: str,
        position: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing annotation.

        Args:
            annotation_id: Annotation to update
            content: New content
            position: New position (optional)

        Returns:
            True if update successful
        """
        # Find annotation
        for doc_annotations in self.document_annotations.values():
            for annotation in doc_annotations:
                if annotation.annotation_id == annotation_id:
                    annotation.content = content
                    annotation.updated_at = datetime.utcnow()

                    if position:
                        annotation.position = position

                    # Broadcast update
                    operation = {
                        'type': 'annotation',
                        'action': 'update',
                        'annotation': annotation.__dict__,
                        'timestamp': datetime.utcnow().isoformat()
                    }

                    asyncio.create_task(self._broadcast_to_session(
                        annotation.document_id, operation
                    ))

                    return True

        return False

    @handle_errors(operation="resolve_annotation", component="realtime_engine")
    def resolve_annotation(self, annotation_id: str) -> bool:
        """Resolve annotation.

        Args:
            annotation_id: Annotation to resolve

        Returns:
            True if resolve successful
        """
        # Find and resolve annotation
        for doc_annotations in self.document_annotations.values():
            for annotation in doc_annotations:
                if annotation.annotation_id == annotation_id:
                    annotation.is_resolved = True
                    annotation.updated_at = datetime.utcnow()

                    # Broadcast resolution
                    operation = {
                        'type': 'annotation',
                        'action': 'resolve',
                        'annotation': annotation.__dict__,
                        'timestamp': datetime.utcnow().isoformat()
                    }

                    asyncio.create_task(self._broadcast_to_session(
                        annotation.document_id, operation
                    ))

                    return True

        return False

    @handle_errors(operation="apply_collaborative_edit", component="realtime_engine")
    def apply_collaborative_edit(
        self,
        session_id: str,
        user_id: str,
        operation_type: str,
        position: Dict[str, Any],
        content: str
    ) -> str:
        """Apply collaborative edit to document.

        Args:
            session_id: Collaboration session ID
            user_id: User making the edit
            operation_type: Type of edit operation
            position: Position in document
            content: Content being edited

        Returns:
            Edit ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Create edit operation
        edit_id = f"edit_{uuid.uuid4().hex}"

        edit = CollaborativeEdit(
            edit_id=edit_id,
            session_id=session_id,
            user_id=user_id,
            operation_type=operation_type,
            position=position,
            content=content
        )

        # Queue edit for processing
        operation = {
            'type': 'edit',
            'edit': edit.__dict__,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Add to queue for async processing
        asyncio.create_task(self._broadcast_edit_to_session(session_id, operation))

        # Update session activity
        session.last_activity = datetime.utcnow()

        return edit_id

    async def _broadcast_to_session(self, document_id: str, operation: Dict[str, Any]) -> None:
        """Broadcast operation to all session participants.

        Args:
            document_id: Document ID
            operation: Operation to broadcast
        """
        # Find all sessions for this document
        document_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session.document_id == document_id and session.is_active
        ]

        # Broadcast to all sessions
        for session_id in document_sessions:
            await self._broadcast_edit_to_session(session_id, operation)

    async def _broadcast_edit_to_session(self, session_id: str, operation: Dict[str, Any]) -> None:
        """Broadcast edit to specific session.

        Args:
            session_id: Session to broadcast to
            operation: Operation to broadcast
        """
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]

        # In a real implementation, this would send to WebSocket clients
        # For now, just log the operation
        self.logger.info(f"Broadcasting operation to session {session_id}: {operation['type']}")

        # Simulate broadcasting to connected clients
        for user_id in session.participants.keys():
            if user_id in self.connected_clients:
                client_info = self.connected_clients[user_id]
                # Send to WebSocket connection
                await self._send_to_client(client_info, operation)

    async def _send_to_client(self, client_info: Dict[str, Any], message: Dict[str, Any]) -> None:
        """Send message to specific client.

        Args:
            client_info: Client connection information
            message: Message to send
        """
        # This would send to actual WebSocket connection
        # For now, just log
        self.logger.debug(f"Would send to client: {message}")

    def register_client(self, user_id: str, client_info: Dict[str, Any]) -> None:
        """Register client connection.

        Args:
            user_id: User ID
            client_info: Client connection information
        """
        self.connected_clients[user_id] = client_info
        self.logger.info(f"Client registered for user {user_id}")

    def unregister_client(self, user_id: str) -> None:
        """Unregister client connection.

        Args:
            user_id: User ID
        """
        if user_id in self.connected_clients:
            del self.connected_clients[user_id]
            self.logger.info(f"Client unregistered for user {user_id}")

    def get_document_annotations(self, document_id: str) -> List[DocumentAnnotation]:
        """Get all annotations for document.

        Args:
            document_id: Document ID

        Returns:
            List of annotations
        """
        return self.document_annotations.get(document_id, [])

    def get_user_annotations(self, user_id: str, document_id: str) -> List[DocumentAnnotation]:
        """Get annotations by user for document.

        Args:
            user_id: User ID
            document_id: Document ID

        Returns:
            List of user annotations
        """
        all_annotations = self.get_document_annotations(document_id)
        return [ann for ann in all_annotations if ann.user_id == user_id]

    def create_document_version(
        self,
        document_id: str,
        content_snapshot: str,
        changes: List[CollaborativeEdit],
        created_by: str,
        description: Optional[str] = None
    ) -> str:
        """Create new document version.

        Args:
            document_id: Document ID
            content_snapshot: Document content snapshot
            changes: Changes in this version
            created_by: User who created version
            description: Version description

        Returns:
            Version ID
        """
        # Get existing versions
        existing_versions = self.document_versions.get(document_id, [])

        # Calculate version number
        version_number = len(existing_versions) + 1

        version_id = f"version_{document_id}_{version_number}"

        version = DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            version_number=version_number,
            content_snapshot=content_snapshot,
            changes=changes,
            created_by=created_by,
            description=description
        )

        self.document_versions[document_id].append(version)

        self.logger.info(f"Created version {version_number} for document {document_id}")
        return version_id

    def get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions for document.

        Args:
            document_id: Document ID

        Returns:
            List of document versions
        """
        return self.document_versions.get(document_id, [])

    def get_version_diff(self, document_id: str, from_version: int, to_version: int) -> Dict[str, Any]:
        """Get diff between two versions.

        Args:
            document_id: Document ID
            from_version: Starting version number
            to_version: Ending version number

        Returns:
            Diff information
        """
        versions = self.get_document_versions(document_id)

        from_ver = next((v for v in versions if v.version_number == from_version), None)
        to_ver = next((v for v in versions if v.version_number == to_version), None)

        if not from_ver or not to_ver:
            return {}

        # Simple diff calculation
        diff = {
            'from_version': from_version,
            'to_version': to_version,
            'changes_count': len(to_ver.changes) - len(from_ver.changes),
            'created_by': to_ver.created_by,
            'description': to_ver.description,
            'timestamp': to_ver.created_at.isoformat()
        }

        return diff

    def get_collaboration_stats(self, document_id: str) -> Dict[str, Any]:
        """Get collaboration statistics for document.

        Args:
            document_id: Document ID

        Returns:
            Collaboration statistics
        """
        annotations = self.get_document_annotations(document_id)
        versions = self.get_document_versions(document_id)

        # Count annotation types
        annotation_types = defaultdict(int)
        for annotation in annotations:
            annotation_types[annotation.annotation_type] += 1

        # Count participants
        document_sessions = [
            session for session in self.active_sessions.values()
            if session.document_id == document_id
        ]

        total_participants = sum(len(session.participants) for session in document_sessions)

        return {
            'total_annotations': len(annotations),
            'annotation_types': dict(annotation_types),
            'total_versions': len(versions),
            'active_sessions': len(document_sessions),
            'total_participants': total_participants,
            'last_activity': max(
                (session.last_activity for session in document_sessions),
                default=None
            )
        }

    def resolve_edit_conflict(
        self,
        session_id: str,
        conflicting_edits: List[CollaborativeEdit]
    ) -> CollaborativeEdit:
        """Resolve edit conflict using configured strategy.

        Args:
            session_id: Session with conflict
            conflicting_edits: List of conflicting edits

        Returns:
            Resolved edit
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        conflict_strategy = session.settings.get('conflict_resolution', 'last_write_wins')

        if conflict_strategy == 'last_write_wins':
            # Use most recent edit
            return max(conflicting_edits, key=lambda e: e.timestamp)
        elif conflict_strategy == 'first_write_wins':
            # Use first edit
            return min(conflicting_edits, key=lambda e: e.timestamp)
        elif conflict_strategy == 'merge':
            # Attempt to merge edits
            return self._merge_conflicting_edits(conflicting_edits)
        else:
            # Default to last write wins
            return max(conflicting_edits, key=lambda e: e.timestamp)

    def _merge_conflicting_edits(self, edits: List[CollaborativeEdit]) -> CollaborativeEdit:
        """Attempt to merge conflicting edits.

        Args:
            edits: List of conflicting edits

        Returns:
            Merged edit
        """
        if not edits:
            raise ValueError("No edits to merge")

        # Simple merge strategy - combine non-overlapping edits
        merged_content = ""
        merged_position = edits[0].position.copy()

        for edit in edits:
            if edit.operation_type == 'insert':
                merged_content += edit.content
            # Add more sophisticated merging logic here

        return CollaborativeEdit(
            edit_id=f"merged_{uuid.uuid4().hex}",
            session_id=edits[0].session_id,
            user_id="system_merge",
            operation_type="merge",
            position=merged_position,
            content=merged_content
        )

    def get_session_activity(self, session_id: str) -> Dict[str, Any]:
        """Get activity information for session.

        Args:
            session_id: Session ID

        Returns:
            Session activity data
        """
        if session_id not in self.active_sessions:
            return {}

        session = self.active_sessions[session_id]

        return {
            'session_id': session_id,
            'document_id': session.document_id,
            'participant_count': len(session.participants),
            'participants': [
                {
                    'user_id': user.id,
                    'username': user.username
                }
                for user in session.participants.values()
            ],
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'is_active': session.is_active,
            'settings': session.settings
        }

    def end_collaboration_session(self, session_id: str) -> bool:
        """End collaboration session.

        Args:
            session_id: Session to end

        Returns:
            True if ended successfully
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        session.is_active = False

        # Notify all participants
        operation = {
            'type': 'session_end',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        asyncio.create_task(self._broadcast_edit_to_session(session_id, operation))

        self.logger.info(f"Ended collaboration session: {session_id}")
        return True

    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 60) -> int:
        """Clean up inactive collaboration sessions.

        Args:
            max_inactive_minutes: Maximum inactive time in minutes

        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        inactive_sessions = []

        for session_id, session in self.active_sessions.items():
            if session.is_active:
                inactive_time = current_time - session.last_activity
                if inactive_time.total_seconds() > (max_inactive_minutes * 60):
                    inactive_sessions.append(session_id)

        # End inactive sessions
        for session_id in inactive_sessions:
            self.end_collaboration_session(session_id)

        if inactive_sessions:
            self.logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")

        return len(inactive_sessions)

    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time engine statistics.

        Returns:
            Engine statistics
        """
        active_sessions = len([
            s for s in self.active_sessions.values() if s.is_active
        ])

        total_participants = sum(
            len(s.participants) for s in self.active_sessions.values()
        )

        return {
            'total_sessions': len(self.active_sessions),
            'active_sessions': active_sessions,
            'total_participants': total_participants,
            'connected_clients': len(self.connected_clients),
            'total_annotations': sum(len(anns) for anns in self.document_annotations.values()),
            'total_versions': sum(len(vers) for vers in self.document_versions.values()),
            'timestamp': datetime.utcnow().isoformat()
        }


class CommentSystem:
    """Comment and discussion system for documents."""

    def __init__(self):
        """Initialize comment system."""
        self.logger = logging.getLogger(__name__)

        # Comments storage
        self.document_comments: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.comment_threads: Dict[str, List[str]] = defaultdict(list)

    @handle_errors(operation="add_comment", component="comment_system")
    def add_comment(
        self,
        document_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
        position: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add comment to document.

        Args:
            document_id: Document ID
            user_id: User adding comment
            content: Comment content
            parent_comment_id: Parent comment for threading
            position: Position in document

        Returns:
            Comment ID
        """
        comment_id = f"comment_{uuid.uuid4().hex}"

        comment = {
            'comment_id': comment_id,
            'document_id': document_id,
            'user_id': user_id,
            'content': content,
            'parent_comment_id': parent_comment_id,
            'position': position,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'is_resolved': False,
            'replies': []
        }

        self.document_comments[document_id].append(comment)

        # Add to thread if parent exists
        if parent_comment_id:
            self.comment_threads[parent_comment_id].append(comment_id)
        else:
            self.comment_threads[comment_id] = []

        self.logger.info(f"Added comment {comment_id} to document {document_id}")
        return comment_id

    def get_document_comments(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all comments for document.

        Args:
            document_id: Document ID

        Returns:
            List of comments
        """
        return self.document_comments.get(document_id, [])

    def resolve_comment(self, comment_id: str) -> bool:
        """Resolve comment.

        Args:
            comment_id: Comment to resolve

        Returns:
            True if resolved successfully
        """
        # Find and resolve comment
        for comments in self.document_comments.values():
            for comment in comments:
                if comment['comment_id'] == comment_id:
                    comment['is_resolved'] = True
                    comment['updated_at'] = datetime.utcnow().isoformat()
                    return True

        return False

    def get_comment_thread(self, comment_id: str) -> List[Dict[str, Any]]:
        """Get comment thread including replies.

        Args:
            comment_id: Root comment ID

        Returns:
            List of comments in thread
        """
        thread = []

        # Find root comment
        root_comment = None
        for comments in self.document_comments.values():
            for comment in comments:
                if comment['comment_id'] == comment_id:
                    root_comment = comment
                    break

        if not root_comment:
            return thread

        thread.append(root_comment)

        # Add replies recursively
        self._add_comment_replies(comment_id, thread)

        return thread

    def _add_comment_replies(self, comment_id: str, thread: List[Dict[str, Any]]) -> None:
        """Add replies to comment thread."""
        reply_ids = self.comment_threads.get(comment_id, [])

        for reply_id in reply_ids:
            # Find reply comment
            reply_comment = None
            for comments in self.document_comments.values():
                for comment in comments:
                    if comment['comment_id'] == reply_id:
                        reply_comment = comment
                        break

            if reply_comment:
                thread.append(reply_comment)
                # Add nested replies
                self._add_comment_replies(reply_id, thread)


class NotificationSystem:
    """Notification system for real-time collaboration."""

    def __init__(self):
        """Initialize notification system."""
        self.logger = logging.getLogger(__name__)

        # Notification storage
        self.user_notifications: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.notification_settings: Dict[str, Dict[str, Any]] = {}

    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send notification to user.

        Args:
            user_id: User to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            metadata: Additional metadata

        Returns:
            Notification ID
        """
        notification_id = f"notification_{uuid.uuid4().hex}"

        notification = {
            'notification_id': notification_id,
            'user_id': user_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'is_read': False,
            'read_at': None
        }

        self.user_notifications[user_id].append(notification)

        # Keep only recent notifications (last 100 per user)
        if len(self.user_notifications[user_id]) > 100:
            self.user_notifications[user_id] = self.user_notifications[user_id][-100:]

        self.logger.info(f"Sent {notification_type} notification to user {user_id}")
        return notification_id

    def send_collaboration_notification(
        self,
        session_id: str,
        notification_type: str,
        title: str,
        message: str,
        exclude_user_id: Optional[str] = None
    ) -> None:
        """Send notification to all session participants.

        Args:
            session_id: Session ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            exclude_user_id: User to exclude from notification
        """
        # This would get session participants and send notifications
        # For now, just log
        self.logger.info(f"Would send collaboration notification: {title}")

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get notifications for user.

        Args:
            user_id: User ID
            unread_only: Return only unread notifications
            limit: Maximum notifications

        Returns:
            List of notifications
        """
        notifications = self.user_notifications.get(user_id, [])

        if unread_only:
            notifications = [n for n in notifications if not n['is_read']]

        # Sort by creation time (newest first)
        notifications.sort(key=lambda x: x['created_at'], reverse=True)

        return notifications[:limit]

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read.

        Args:
            notification_id: Notification to mark
            user_id: User ID

        Returns:
            True if marked successfully
        """
        notifications = self.user_notifications.get(user_id, [])

        for notification in notifications:
            if notification['notification_id'] == notification_id:
                notification['is_read'] = True
                notification['read_at'] = datetime.utcnow().isoformat()
                return True

        return False

    def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all user notifications as read.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked
        """
        notifications = self.user_notifications.get(user_id, [])
        marked_count = 0

        for notification in notifications:
            if not notification['is_read']:
                notification['is_read'] = True
                notification['read_at'] = datetime.utcnow().isoformat()
                marked_count += 1

        return marked_count

    def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for user.

        Args:
            user_id: User ID

        Returns:
            Notification statistics
        """
        notifications = self.user_notifications.get(user_id, [])

        total_count = len(notifications)
        unread_count = len([n for n in notifications if not n['is_read']])

        # Count by type
        type_counts = defaultdict(int)
        for notification in notifications:
            type_counts[notification['type']] += 1

        return {
            'user_id': user_id,
            'total_notifications': total_count,
            'unread_notifications': unread_count,
            'notifications_by_type': dict(type_counts),
            'oldest_notification': notifications[-1]['created_at'] if notifications else None,
            'newest_notification': notifications[0]['created_at'] if notifications else None
        }


class ChangeTrackingSystem:
    """System for tracking document changes and history."""

    def __init__(self):
        """Initialize change tracking system."""
        self.logger = logging.getLogger(__name__)

        # Change history
        self.change_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def track_change(
        self,
        document_id: str,
        user_id: str,
        change_type: str,
        description: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track document change.

        Args:
            document_id: Document ID
            user_id: User making the change
            change_type: Type of change
            description: Change description
            before_state: State before change
            after_state: State after change

        Returns:
            Change ID
        """
        change_id = f"change_{uuid.uuid4().hex}"

        change = {
            'change_id': change_id,
            'document_id': document_id,
            'user_id': user_id,
            'change_type': change_type,
            'description': description,
            'before_state': before_state,
            'after_state': after_state,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.change_history[document_id].append(change)

        # Keep only recent changes (last 1000 per document)
        if len(self.change_history[document_id]) > 1000:
            self.change_history[document_id] = self.change_history[document_id][-1000:]

        self.logger.info(f"Tracked change {change_id} for document {document_id}")
        return change_id

    def get_document_change_history(
        self,
        document_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get change history for document.

        Args:
            document_id: Document ID
            limit: Maximum changes to return

        Returns:
            List of changes
        """
        changes = self.change_history.get(document_id, [])

        # Sort by timestamp (newest first)
        changes.sort(key=lambda x: x['timestamp'], reverse=True)

        return changes[:limit]

    def get_change_diff(self, change_id: str) -> Dict[str, Any]:
        """Get detailed diff for specific change.

        Args:
            change_id: Change ID

        Returns:
            Change diff information
        """
        # Find change
        for changes in self.change_history.values():
            for change in changes:
                if change['change_id'] == change_id:
                    return self._calculate_change_diff(change)

        return {}

    def _calculate_change_diff(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate diff for change."""
        diff = {
            'change_id': change['change_id'],
            'change_type': change['change_type'],
            'description': change['description'],
            'timestamp': change['timestamp'],
            'diff_details': {}
        }

        # Calculate state differences
        before_state = change.get('before_state', {})
        after_state = change.get('after_state', {})

        # Simple diff calculation
        all_keys = set(before_state.keys()) | set(after_state.keys())

        for key in all_keys:
            before_value = before_state.get(key)
            after_value = after_state.get(key)

            if before_value != after_value:
                diff['diff_details'][key] = {
                    'before': before_value,
                    'after': after_value,
                    'change_type': 'modified'
                }

        return diff

    def get_user_change_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get change summary for user.

        Args:
            user_id: User ID
            days: Days to look back

        Returns:
            Change summary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_changes = []

        # Find all changes by user
        for changes in self.change_history.values():
            for change in changes:
                if change['user_id'] == user_id:
                    change_time = datetime.fromisoformat(change['timestamp'])
                    if change_time >= cutoff_date:
                        user_changes.append(change)

        # Group by change type
        change_types = defaultdict(int)
        for change in user_changes:
            change_types[change['change_type']] += 1

        return {
            'user_id': user_id,
            'total_changes': len(user_changes),
            'changes_by_type': dict(change_types),
            'time_period_days': days,
            'most_recent_change': user_changes[0]['timestamp'] if user_changes else None
        }


class RealTimeCollaborationSystem:
    """Main real-time collaboration system."""

    def __init__(self):
        """Initialize collaboration system."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.realtime_engine = RealTimeEngine()
        self.comment_system = CommentSystem()
        self.notification_system = NotificationSystem()
        self.change_tracking = ChangeTrackingSystem()

    def create_collaboration_session(
        self,
        document_id: str,
        creator_user_id: str,
        max_participants: int = 10
    ) -> str:
        """Create collaboration session.

        Args:
            document_id: Document ID
            creator_user_id: User creating session
            max_participants: Maximum participants

        Returns:
            Session ID
        """
        return self.realtime_engine.create_collaboration_session(
            document_id, creator_user_id, max_participants
        )

    def add_document_annotation(
        self,
        document_id: str,
        user_id: str,
        annotation_type: str,
        content: str,
        position: Dict[str, Any]
    ) -> str:
        """Add annotation to document.

        Args:
            document_id: Document ID
            user_id: User ID
            annotation_type: Type of annotation
            content: Annotation content
            position: Position in document

        Returns:
            Annotation ID
        """
        return self.realtime_engine.add_annotation(
            document_id, user_id, annotation_type, content, position
        )

    def add_comment(
        self,
        document_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None
    ) -> str:
        """Add comment to document.

        Args:
            document_id: Document ID
            user_id: User ID
            content: Comment content
            parent_comment_id: Parent comment for threading

        Returns:
            Comment ID
        """
        return self.comment_system.add_comment(
            document_id, user_id, content, parent_comment_id
        )

    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str
    ) -> str:
        """Send notification to user.

        Args:
            user_id: User ID
            notification_type: Notification type
            title: Notification title
            message: Notification message

        Returns:
            Notification ID
        """
        return self.notification_system.send_notification(
            user_id, notification_type, title, message
        )

    def track_document_change(
        self,
        document_id: str,
        user_id: str,
        change_type: str,
        description: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track document change.

        Args:
            document_id: Document ID
            user_id: User ID
            change_type: Type of change
            description: Change description
            before_state: State before change
            after_state: State after change

        Returns:
            Change ID
        """
        return self.change_tracking.track_change(
            document_id, user_id, change_type, description, before_state, after_state
        )

    def get_collaboration_overview(self, document_id: str) -> Dict[str, Any]:
        """Get collaboration overview for document.

        Args:
            document_id: Document ID

        Returns:
            Collaboration overview
        """
        return {
            'realtime_stats': self.realtime_engine.get_collaboration_stats(document_id),
            'comments': self.comment_system.get_document_comments(document_id),
            'annotations': self.realtime_engine.get_document_annotations(document_id),
            'versions': self.realtime_engine.get_document_versions(document_id),
            'change_history': self.change_tracking.get_document_change_history(document_id, 10)
        }

    def cleanup_inactive_sessions(self) -> int:
        """Clean up inactive collaboration sessions.

        Returns:
            Number of sessions cleaned up
        """
        return self.realtime_engine.cleanup_inactive_sessions()

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide collaboration statistics.

        Returns:
            System statistics
        """
        return {
            'realtime_engine': self.realtime_engine.get_realtime_stats(),
            'total_comments': sum(len(comments) for comments in self.comment_system.document_comments.values()),
            'total_notifications': sum(len(notifications) for notifications in self.notification_system.user_notifications.values()),
            'total_changes': sum(len(changes) for changes in self.change_tracking.change_history.values())
        }


# Factory function

def create_collaboration_system() -> RealTimeCollaborationSystem:
    """Create complete real-time collaboration system.

    Returns:
        Configured collaboration system
    """
    return RealTimeCollaborationSystem()


# Integration functions

def create_collaboration_session(
    document_id: str,
    creator_user_id: str,
    max_participants: int = 10
) -> str:
    """Create collaboration session (convenience function).

    Args:
        document_id: Document ID
        creator_user_id: User creating session
        max_participants: Maximum participants

    Returns:
        Session ID
    """
    system = create_collaboration_system()
    return system.create_collaboration_session(document_id, creator_user_id, max_participants)


def add_document_comment(
    document_id: str,
    user_id: str,
    content: str,
    parent_comment_id: Optional[str] = None
) -> str:
    """Add comment to document (convenience function).

    Args:
        document_id: Document ID
        user_id: User ID
        content: Comment content
        parent_comment_id: Parent comment for threading

    Returns:
        Comment ID
    """
    system = create_collaboration_system()
    return system.add_comment(document_id, user_id, content, parent_comment_id)


def send_collaboration_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str
) -> str:
    """Send collaboration notification (convenience function).

    Args:
        user_id: User ID
        notification_type: Notification type
        title: Notification title
        message: Notification message

    Returns:
        Notification ID
    """
    system = create_collaboration_system()
    return system.send_notification(user_id, notification_type, title, message)
