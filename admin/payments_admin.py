# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from payments import get_pending_payments, approve_payment, reject_payment, get_payment_stats


async def show_payments_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payments management menu"""
    query = update.callback_query
    if query:
        await query.answer()
    
    stats = get_payment_stats()
    
    text = f"💳 *To'lovlar boshqaruvi*\n\n"
    text += f"⏳ Kutilmoqda: {stats['pending']}\n"
    text += f"✅ Tasdiqlangan: {stats['approved']}\n"
    text += f"❌ Rad etilgan: {stats['rejected']}\n\n"
    text += f"💎 Premium: {stats['premium_count']}\n"
    text += f"📚 Kurslar: {stats['course_count']}\n"
    text += f"📞 Konsultatsiya: {stats['consult_count']}\n\n"
    text += f"💰 Jami daromad: ${stats['total_revenue']}"
    
    buttons = [
        [InlineKeyboardButton("⏳ Kutayotgan to'lovlar", callback_data="ap:payments:pending")],
        [InlineKeyboardButton("✅ Tasdiqlangan", callback_data="ap:payments:approved")],
        [InlineKeyboardButton("📊 Statistika", callback_data="ap:payments:stats")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="ap:home")]
    ]
    
    if query:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )


async def show_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending payments"""
    query = update.callback_query
    await query.answer()
    
    pending = get_pending_payments()
    
    if not pending:
        text = "⏳ Kutayotgan to'lovlar yo'q"
        buttons = [[InlineKeyboardButton("🔙 Orqaga", callback_data="ap:payments")]]
    else:
        text = "⏳ *Kutayotgan to'lovlar:*\n\n"
        buttons = []
        
        for pay_id, payment in list(pending.items())[:10]:
            user_id = payment.get("user_id")
            username = payment.get("username", "-")
            first_name = payment.get("first_name", "User")
            payment_type = payment.get("type")
            amount = payment.get("amount")
            
            if payment_type == "premium":
                type_emoji = "💎"
                type_text = "Premium"
            elif payment_type == "course":
                type_emoji = "📚"
                course_id = payment.get("course_id", "")
                type_text = f"Kurs: {course_id}"
            else:
                type_emoji = "📞"
                type_text = "Konsultatsiya"
            
            text += f"{type_emoji} {first_name} (@{username})\n"
            text += f"💰 ${amount} - {type_text}\n"
            text += f"🆔 {user_id} | ID: {pay_id}\n\n"
            
            buttons.append([
                InlineKeyboardButton(f"✅ {first_name[:15]}", callback_data=f"ap:pay:approve:{pay_id}"),
                InlineKeyboardButton(f"❌", callback_data=f"ap:pay:reject:{pay_id}")
            ])
        
        buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="ap:payments")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )


async def handle_payment_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, pay_id: str):
    """Handle payment approval/rejection"""
    query = update.callback_query
    await query.answer()
    
    if action == "approve":
        # Import here to avoid circular dependency
        from bot import handle_admin_approve_internal
        await handle_admin_approve_internal(context, pay_id)
        await query.edit_message_text("✅ To'lov tasdiqlandi!")
        
    elif action == "reject":
        from bot import handle_admin_reject_internal
        await handle_admin_reject_internal(context, pay_id)
        await query.edit_message_text("❌ To'lov rad etildi!")
    
    # Return to pending payments list
    await show_pending_payments(update, context)
