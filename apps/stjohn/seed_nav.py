from models import engine, Base, NavbarItem, SessionLocal
Base.metadata.create_all(bind=engine)
db = SessionLocal()
if not db.query(NavbarItem).first():
    items = [
        NavbarItem(title='About', url='#about', sort_order=1),
        NavbarItem(title='Ministries', url='#ministries', sort_order=2),
        NavbarItem(title='Worship', url='#worship', sort_order=3),
        NavbarItem(title='Events', url='#events', sort_order=4),
        NavbarItem(title='Contact', url='#contact', sort_order=5),
        NavbarItem(title='Give', url='https://www.stjohnjoliet.org/give', sort_order=6),
        NavbarItem(title='Member Portal', url='https://www.stjohnjoliet.org/pages/member-portal', sort_order=7),
        NavbarItem(title='Visit Us', url='#contact', sort_order=8, is_cta=True)
    ]
    db.add_all(items)
    db.commit()
db.close()
print("Navbar seeded successfully")
