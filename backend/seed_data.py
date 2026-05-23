"""
种子脚本：从静态模板导入收藏数据到数据库
运行：python3 seed_data.py
"""
import sys
import os

# 确保能找到 backend 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from extensions import db
from models.user import User
from models.group import Group
from models.bookmark import Bookmark
import bcrypt

# ====== 种子数据 ======
groups_data = [
    {
        'name': '绩效核算',
        'icon': '',
        'bookmarks': [
            {'title': '人员花名册', 'url': 'https://bi.sankuai.com/dashboard/163742', 'description': '人员花名册，薪资核算的基础，每月26日需核验自己账号的权限，查看是否有新增业务线需要申请，时间范围选择：上月26-本月25日，绩效核算不涉及职能岗，下载花名册后需剔除。', 'bg_color': '#4285F4'},
            {'title': '坐席工时&指标数据', 'url': 'https://bi.sankuai.com/dashboard/163811', 'description': '人员工时、数据总表，每月27日下载绩效月工时统计（含补录）、绩效宽表以及支援时长统计，时间范围选择上月26-本月25日。', 'bg_color': '#0078D4'},
            {'title': '出勤统计表', 'url': 'https://bi.sankuai.com/dashboard/208178', 'description': '坐席+职能岗的出勤，可自由选择日期，绩效核算选择绩效月周期进行下载，用于绩效表激励关于出勤方面的指标达成核验。', 'bg_color': '#000000'},
            {'title': '质检达成数据', 'url': 'https://bi.sankuai.com/dashboard/164399', 'description': '坐席各种质检扣罚的统计表，每月数据就绪时间一般在28号下班前（有时会延迟到29号，以群内景晨通知为准）。', 'bg_color': '#2932E1'},
            {'title': '绩效和激励方案文档', 'url': 'https://km.sankuai.com/collabpage/2710283349', 'description': '所有业务线的绩效方案与激励方案汇总，需了解每条业务线的具体绩效计算规则，尤其注意激励方案，每个月都会变动，及时更新规则。', 'bg_color': '#5CB85C'},
        ]
    },
    {
        'name': 'TO-C核算',
        'icon': '',
        'bookmarks': [
            {'title': '人员花名册', 'url': 'https://bi.sankuai.com/dashboard/163742', 'description': '次月1日重新下载人员花名册，需重新核验自己账号的权限，查看是否有新增业务线需要申请，时间范围选择：上月26-本月月底，需带职能岗。', 'bg_color': '#1DA1F2'},
            {'title': '出勤统计表', 'url': 'https://bi.sankuai.com/dashboard/208178', 'description': '次月2日等待所有业务线补录完成后，于3日重新下载出勤统计表，选择自然月全月时间范围进行下载。', 'bg_color': '#0A66C2'},
            {'title': '班次补贴统计表', 'url': 'https://bi.sankuai.com/dashboard/164508', 'description': '下载自然月班次补贴明细（含补录）。', 'bg_color': '#1877F2'},
            {'title': '正负工时统计', 'url': 'https://bi.sankuai.com/dashboard/164536', 'description': '正负工时结算为季度结算（3、6、9、12月），如人员未离职正工时正常季度结算，负工时只统计不结算。', 'bg_color': '#E4405F'},
            {'title': '星火燎原激励方案', 'url': 'https://km.sankuai.com/collabpage/2707395920', 'description': '本激励加入TO-C的结算中，现阶段本激励适用于2025年7月所有满足条件的业务线。', 'bg_color': '#E6162D'},
            {'title': '全业务大夜入职激励方案', 'url': '#', 'description': '全业务大夜业务线员工入职满30天给500元，入职满60天再给500元。', 'bg_color': '#E6162D'},
            {'title': 'TO-C终版上传', 'url': 'https://shenpi.sankuai.com/p/submit?pdId=10840', 'description': '每月10日之前将确定好的TO-C终版上传至本链接。', 'bg_color': '#E6162D'},
        ]
    },
    {
        'name': 'TO-B核算',
        'icon': '',
        'bookmarks': [
            {'title': '商务指标表', 'url': 'https://bi.sankuai.com/dashboard/165030', 'description': '客服&职能岗招聘达成的各项数据汇总。', 'bg_color': '#181717'},
            {'title': '流失&招聘质量', 'url': 'https://bi.sankuai.com/dashboard/66780', 'description': '流失率、招聘质量明的各项数据汇总。', 'bg_color': '#4285F4'},
        ]
    },
    {
        'name': '规则汇总',
        'icon': '',
        'bookmarks': [
            {'title': '石家庄薪酬方案与结费规则', 'url': 'https://km.sankuai.com/collabpage/2704007592', 'description': '石家庄职场各项结算的基本规则（宣导版本）。', 'bg_color': '#0056D3'},
            {'title': 'TO-C结算流程', 'url': 'https://km.sankuai.com/collabpage/2210389008', 'description': 'TO-C流程及时间节点详解，需在规定时间内提交对应的数据。', 'bg_color': '#EC5252'},
            {'title': 'TO-B结算流程', 'url': 'https://km.sankuai.com/collabpage/2211440479', 'description': 'TO-B流程及时间节点详解，需在规定时间内提交对应的数据。', 'bg_color': '#F48024'},
        ]
    },
]


def seed():
    app = create_app()
    with app.app_context():
        # 找 admin 用户（id=1）
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            # 如果没有管理员，创建一个
            hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = User(username='admin', password_hash=hashed, nickname='超级管理员', role='admin')
            db.session.add(admin)
            db.session.commit()
            print(f'✅ 创建管理员: admin / admin123')
        else:
            print(f'✅ 使用已有管理员: {admin.username} (id={admin.id})')

        # 先清空已有数据（避免重复导入）
        Bookmark.query.filter_by(user_id=admin.id).delete()
        Group.query.filter_by(user_id=admin.id).delete()
        db.session.commit()

        sort_order = 0
        total = 0
        for gd in groups_data:
            sort_order += 1
            group = Group(user_id=admin.id, name=gd['name'], sort_order=sort_order)
            db.session.add(group)
            db.session.flush()  # 获取 group.id
            print(f'  📂 分组: {group.name}')

            for bd in gd['bookmarks']:
                bm = Bookmark(
                    user_id=admin.id,
                    group_id=group.id,
                    title=bd['title'],
                    url=bd['url'],
                    description=bd.get('description', ''),
                    bg_color=bd.get('bg_color', '#6C5CE7'),
                    icon=bd.get('icon', ''),
                    sort_order=0,
                )
                db.session.add(bm)
                total += 1

        db.session.commit()
        print(f'\n✅ 导入完成！共 {len(groups_data)} 个分组，{total} 条收藏')


if __name__ == '__main__':
    seed()
