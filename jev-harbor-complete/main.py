"""Command-line front end for the Jev ticketing demo.  Run:  python main.py"""
from app.models import STATUSES, Ticket
from app.service import TicketService


def ask(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("  This field is required.")


def show_row(t: Ticket) -> None:
    flags = ("ESC " if t.escalated else "") + ("REVIEW" if t.needs_review else "")
    print(f"{t.id:<11}{t.priority_label:<10}{t.status:<13}"
          f"{t.assigned_queue:<21}{t.title[:32]:<34}{flags}")


def show_detail(t: Ticket) -> None:
    tr = t.triage
    print(f"\n{t.id}  |  {t.title}")
    print(f"  From:        {t.customer_email}   Created: {t.created_at}")
    print(f"  Status:      {t.status}")
    print(f"  Description: {t.description}")
    print("  -- Routing --")
    print(f"  Queue:       {t.assigned_queue}")
    print(f"  Priority:    {t.priority_label} (respond within {t.sla_hours}h)")
    print(f"  Escalated:   {'yes' if t.escalated else 'no'}"
          f"   Needs review: {'yes' if t.needs_review else 'no'}")
    if tr:
        print(f"  -- Model decisions ({tr.model}) --")
        print(f"  Category:    {tr.category} (confidence {tr.category_confidence:.2f})")
        print(f"  Priority:    {tr.priority_score:.2f} / 3 (confidence {tr.priority_confidence:.2f})")
        print(f"  Escalate?    P(yes) = {tr.escalate_probability:.2f}")
        print(f"  Refund?      P(yes) = {tr.refund_probability:.2f}")
    print()


def main() -> None:
    service = TicketService()
    print("=" * 60)
    print("  Jev Ticketing System Demo")
    print(f"  Triage engine: {service.mode}")
    print("=" * 60)

    menu = """
1) Create ticket      4) Update status
2) List tickets       5) Load sample tickets
3) View ticket        6) Clear all tickets
q) Quit"""

    try:
        while True:
            print(menu)
            choice = input("> ").strip().lower()

            if choice == "1":
                ticket = service.create_ticket(
                    ask("Title"), ask("Description"), ask("Customer email"))
                print(f"\nCreated {ticket.id}:")
                show_detail(ticket)

            elif choice == "2":
                tickets = service.list_tickets()
                if not tickets:
                    print("No tickets yet. Try option 5 to load samples.")
                    continue
                print(f"\n{'ID':<11}{'Priority':<10}{'Status':<13}{'Queue':<21}{'Title':<34}Flags")
                print("-" * 95)
                for t in tickets:
                    show_row(t)

            elif choice == "3":
                ticket = service.get_ticket(ask("Ticket ID"))
                show_detail(ticket) if ticket else print("Ticket not found.")

            elif choice == "4":
                ticket_id = ask("Ticket ID")
                status = ask(f"New status ({'/'.join(STATUSES)})").lower()
                try:
                    ticket = service.update_status(ticket_id, status)
                    print(f"Updated {ticket.id} -> {status}" if ticket else "Ticket not found.")
                except ValueError as error:
                    print(error)

            elif choice == "5":
                print("Triaging sample tickets...")
                for t in service.load_samples():
                    print(f"  {t.id}: {t.title[:40]:<42} -> {t.assigned_queue} ({t.priority_label})")

            elif choice == "6":
                if input("Delete ALL tickets? (y/n): ").strip().lower() == "y":
                    service.store.clear()
                    print("All tickets deleted.")

            elif choice in ("q", "quit", "exit"):
                break
            else:
                print("Unknown option.")
    finally:
        service.close()
        print("Goodbye!")


if __name__ == "__main__":
    main()
