"""
Makes fake airline emails + the correct answer (JSON) for each one.
Run:  python make_fake_emails.py
Creates: train.jsonl (about 1000 rows) and test.jsonl (about 200 rows)
"""
import json
import random
 
random.seed(42)  # same result every time you run it
 
FIRST = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Arjun", "Kavya", "Rohan", "Isha"]
LAST = ["Sharma", "Patil", "Deshmukh", "Iyer", "Singh", "Kulkarni", "Reddy", "Mehta", "Nair", "Joshi"]
AIRPORTS = ["PNQ", "BOM", "DEL", "BLR", "HYD", "MAA", "CCU", "GOI", "AMD", "COK"]
AIRLINES = ["6E", "AI", "UK", "SG", "QP"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
 
 
def random_pnr():
    return "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
 
 
def random_time():
    return f"{random.randint(0, 23):02d}:{random.choice(['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'])}"
 
 
def shift_time(t, minutes):
    h, m = map(int, t.split(":"))
    total = (h * 60 + m + minutes) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"
 
 
def date_formats(day, month):
    """Same date written in different ways, like real emails."""
    return [f"{day:02d} {MONTHS[month-1]} 2026", f"{day:02d}/{month:02d}/2026", f"{MONTHS[month-1]} {day}, 2026"]
 
 
# ---- Email styles. Each style is a different "airline writing habit" ----
def style_1(d):
    if d["event_type"] == "cancellation":
        return (f"Dear {d['passenger']},\nWe regret to inform you that flight {d['flight_no']} "
                f"from {d['origin']} to {d['destination']} on {d['date']} at {d['old_time']} has been cancelled.\n"
                f"PNR: {d['pnr']}\nPlease contact us to rebook or request a refund.")
    return (f"Dear {d['passenger']},\nYour flight {d['flight_no']} from {d['origin']} to {d['destination']} "
            f"on {d['date']} has been rescheduled. Old departure: {d['old_time']}. New departure: {d['new_time']}.\n"
            f"PNR: {d['pnr']}\nWe apologise for the inconvenience.")
 
 
def style_2(d):
    if d["event_type"] == "cancellation":
        return (f"CANCELLED!! {d['flight_no']} {d['origin']}-{d['destination']} {d['date']}\n"
                f"Pax: {d['passenger'].upper()} | Booking ref {d['pnr']}\nOriginal dep {d['old_time']}. Visit our site to claim refund.")
    return (f"SCHEDULE CHANGE {d['flight_no']} {d['origin']}-{d['destination']} {d['date']}\n"
            f"Pax: {d['passenger'].upper()} | Booking ref {d['pnr']}\nWas {d['old_time']} -> now {d['new_time']}. Please reconfirm.")
 
 
def style_3(d):
    if d["event_type"] == "cancellation":
        return (f"Hi {d['passenger']}, bad news. Your {d['origin']} to {d['destination']} flight "
                f"({d['flight_no']}) on {d['date']} is cancelled. Ref: {d['pnr']}. "
                f"It was due to leave at {d['old_time']}. Tell us if you want a refund or a new flight.")
    return (f"Hi {d['passenger']}, quick update. Your {d['origin']} to {d['destination']} flight "
            f"({d['flight_no']}) on {d['date']} now leaves at {d['new_time']} instead of {d['old_time']}. "
            f"Ref: {d['pnr']}. No action needed unless the new time doesn't suit you.")
 
 
def style_4(d):  # only used in TEST set (airline style the model never saw)
    if d["event_type"] == "cancellation":
        return (f"--- Forwarded message ---\nSubject: Flight Notice\n\nBooking {d['pnr']} / Traveller: {d['passenger']}\n"
                f"Sector: {d['origin']}>{d['destination']}  Flight: {d['flight_no']}  Date: {d['date']}\n"
                f"Status: CNX. Scheduled time {d['old_time']} hrs. Refund or rebooking available.")
    return (f"--- Forwarded message ---\nSubject: Flight Notice\n\nBooking {d['pnr']} / Traveller: {d['passenger']}\n"
            f"Sector: {d['origin']}>{d['destination']}  Flight: {d['flight_no']}  Date: {d['date']}\n"
            f"Status: RETIMED. Earlier {d['old_time']} hrs, revised {d['new_time']} hrs. Please confirm.")
 
 
def style_5(d):  # only used in TEST set
    if d["event_type"] == "cancellation":
        return (f"Namaste {d['passenger']}! Sorry, but {d['flight_no']} ({d['origin']} to {d['destination']}) "
                f"for {d['date']} will not operate. Your code is {d['pnr']}. It was {d['old_time']} departure.")
    return (f"Namaste {d['passenger']}! Please note {d['flight_no']} ({d['origin']} to {d['destination']}) "
            f"on {d['date']} is moved from {d['old_time']} to {d['new_time']}. Your code is {d['pnr']}.")
 
 
TRAIN_STYLES = [style_1, style_2, style_3]
TEST_STYLES = [style_4, style_5, style_3]  # style_3 also in test, plus 2 brand-new styles
 
 
def make_one(style_list):
    origin, destination = random.sample(AIRPORTS, 2)
    day, month = random.randint(1, 28), random.randint(1, 12)
    event_type = random.choice(["schedule_change", "cancellation"])
    old_time = random_time()
    new_time = shift_time(old_time, random.choice([-90, -45, -30, 30, 45, 60, 120, 180]))
    d = {
        "event_type": event_type,
        "passenger": f"{random.choice(FIRST)} {random.choice(LAST)}",
        "pnr": random_pnr(),
        "flight_no": f"{random.choice(AIRLINES)}{random.randint(100, 9999)}",
        "origin": origin,
        "destination": destination,
        "date": random.choice(date_formats(day, month)),
        "old_time": old_time,
        "new_time": new_time if event_type == "schedule_change" else None,
    }
    email = random.choice(style_list)(d)
    return {"email": email, "output": d}
 
 
def write(filename, count, style_list):
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(count):
            f.write(json.dumps(make_one(style_list), ensure_ascii=False) + "\n")
 
 
if __name__ == "__main__":
    write("train.jsonl", 1000, TRAIN_STYLES)
    write("test.jsonl", 200, TEST_STYLES)
    print("Done! Made train.jsonl (1000) and test.jsonl (200)")
    sample = make_one(TRAIN_STYLES)
    print("\nSample email:\n" + sample["email"])
    print("\nCorrect answer:\n" + json.dumps(sample["output"], indent=2))
 