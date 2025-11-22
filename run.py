#!/usr/bin/env python3
import os
from app import create_app, db
from models import User, PFAProject, GuideStage
from werkzeug.security import generate_password_hash

def init_default_data():
    """Initialize default data"""
    try:
        # Create admin user
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                role="admin",
                first_name="Admin",
                last_name="System",
                is_active=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            print("✅ Admin user created")
        
        # Create jury user
        jury = User.query.filter_by(username="jury").first()
        if not jury:
            jury = User(
                username="jury",
                email="jury@example.com",
                role="jury",
                first_name="Jean",
                last_name="Dupont",
                is_active=True
            )
            jury.set_password("jury123")
            db.session.add(jury)
            print("✅ Jury user created")
        
        # Create student user
        student = User.query.filter_by(username="student").first()
        if not student:
            student = User(
                username="student",
                email="student@example.com",
                role="student",
                first_name="Marie",
                last_name="Martin",
                is_active=True
            )
            student.set_password("student123")
            db.session.add(student)
            print("✅ Student user created")
        
        # Create test projects
        if PFAProject.query.count() == 0 and student:
            projects = [
                {
                    'student_id': student.id,
                    'title': 'Application E-commerce React',
                    'description': 'Une application e-commerce moderne avec React et Node.js',
                    'domain': 'web',
                    'technologies': 'React, Node.js, MongoDB, Express',
                    'status': 'published'
                }
            ]
            
            for project_data in projects:
                project = PFAProject(**project_data)
                db.session.add(project)
            
            print("✅ Test projects created")
        
        # Create guide
        if GuideStage.query.count() == 0 and admin:
            guide = GuideStage(
                title="Guide de Stage PFA - Modèle Standard",
                description="Guide de rédaction pour les projets de fin d'études",
                content="STRUCTURE DU RAPPORT PFA...",
                is_active=True,
                created_by=admin.id
            )
            db.session.add(guide)
            print("✅ Guide created")
        
        db.session.commit()
        print("✅ Default data initialized")
        
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.session.rollback()

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        init_default_data()
    
    print("🚀 RemarqPFA started on http://localhost:5000")
    print("📧 Test accounts:")
    print("   Admin: admin@example.com / admin123")
    print("   Jury: jury@example.com / jury123")
    print("   Student: student@example.com / student123")
    
    app.run(debug=True, host='0.0.0.0', port=5000)