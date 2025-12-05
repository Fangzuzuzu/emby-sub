from backend.models import SubscriptionRequest

class ApprovalService:
    def notify_downloader(self, request: SubscriptionRequest):
        """
        Hook to notify downloader (e.g. MoviePilot).
        Currently this is a placeholder for manual processing.
        """
        # TODO: Implement MoviePilot integration here in future.
        print(f"Request {request.id} approved. Ready for download/manual processing. Title: {request.title}")
        pass

approval_service = ApprovalService()


