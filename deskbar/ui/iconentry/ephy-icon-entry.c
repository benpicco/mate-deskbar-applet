/*
 *  Copyright (C) 2003, 2004, 2005  Christian Persch
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the
 *  Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 *  Boston, MA 02111-1307, USA.
 *
 *  Adapted and modified from gtk+ code:
 *
 *  Copyright (C) 1995-1997 Peter Mattis, Spencer Kimball and Josh MacDonald
 *  Modified by the GTK+ Team and others 1997-2005.  See the AUTHORS
 *  file in the gtk+ distribution for a list of people on the GTK+ Team.
 *  See the ChangeLog in the gtk+ distribution files for a list of changes.
 *  These files are distributed with GTK+ at ftp://ftp.gtk.org/pub/gtk/. 
 *
 *  $Id: ephy-icon-entry.c 174 2005-11-04 15:16:03Z rslinckx $
 */

#ifndef COMPILING_TESTICONENTRY
#include "config.h"
#endif

#include "ephy-icon-entry.h"

#include <gtk/gtk.h>

#define EPHY_ICON_ENTRY_GET_PRIVATE(object)(G_TYPE_INSTANCE_GET_PRIVATE ((object), EPHY_TYPE_ICON_ENTRY, EphyIconEntryPrivate))

struct _EphyIconEntryPrivate
{
	GtkWidget *hbox;
};

static GtkWidgetClass *parent_class = NULL;

/* private helper functions */

static gboolean
entry_focus_change_cb (GtkWidget *widget,
		       GdkEventFocus *event,
		       GtkWidget *entry)
{
	gtk_widget_queue_draw (entry);

	return FALSE;
}

static void
ephy_icon_entry_get_borders (GtkWidget *widget,
			     GtkWidget *entry,
			     int *xborder,
			     int *yborder)
{
	int focus_width;
	gboolean interior_focus;
	GtkStyle *style;

	style = gtk_widget_get_style (entry);
	g_return_if_fail (style != NULL);

	gtk_widget_style_get (entry,
			      "focus-line-width", &focus_width,
			      "interior-focus", &interior_focus,
			      NULL);

	*xborder = style->xthickness;
	*yborder = style->ythickness;

	if (!interior_focus)
	{
		*xborder += focus_width;
		*yborder += focus_width;
	}
}

static void
ephy_icon_entry_paint (GtkWidget *widget,
		       GdkEventExpose *event)
{
	EphyIconEntry *entry = EPHY_ICON_ENTRY (widget);
	GtkWidget *entry_widget = entry->entry;
	int x = 0, y = 0, width, height, focus_width;
	gboolean interior_focus;
	GdkWindow *window;
	GtkStyle *style;

	gtk_widget_style_get (entry_widget,
			      "interior-focus", &interior_focus,
			      "focus-line-width", &focus_width,
			      NULL);

	window = gtk_widget_get_window (widget);

	gdk_drawable_get_size (window, &width, &height);

	if (gtk_widget_has_focus (entry_widget) && !interior_focus)
	{
		x += focus_width;
		y += focus_width;
		width -= 2 * focus_width;
		height -= 2 * focus_width;
	}

	style = gtk_widget_get_style (entry_widget);

	gtk_paint_flat_box (style, window,
			    gtk_widget_get_state (entry_widget), GTK_SHADOW_NONE,
			    NULL, entry_widget, "entry_bg", 
			    /* FIXME: was 0, 0 in gtk_entry_expose, but I think this is correct: */
			    x, y, width, height);
     
	gtk_paint_shadow (style, window,
			  GTK_STATE_NORMAL, GTK_SHADOW_IN,
			  NULL, entry_widget, "entry",
			  x, y, width, height);

	if (gtk_widget_has_focus (entry_widget) && !interior_focus)
	{
		x -= focus_width;
		y -= focus_width;
		width += 2 * focus_width;
		height += 2 * focus_width;

		gtk_paint_focus (style, window,
				 gtk_widget_get_state (entry_widget),
				 NULL, entry_widget, "entry",
				 /* FIXME: was 0, 0 in gtk_entry_draw_frame, but I think this is correct: */
				 x, y, width, height);
	}
}

/* Class implementation */

static void
ephy_icon_entry_init (EphyIconEntry *entry)
{
	EphyIconEntryPrivate *priv;
	GtkWidget *widget = (GtkWidget *) entry;

	priv = entry->priv = EPHY_ICON_ENTRY_GET_PRIVATE (entry);

	gtk_widget_set_has_window (widget, TRUE);

	gtk_container_set_border_width (GTK_CONTAINER (entry), 0);

	priv->hbox = gtk_hbox_new (FALSE, /* FIXME */ 0);
	gtk_container_add (GTK_CONTAINER (entry), priv->hbox);

	entry->entry = gtk_entry_new ();
	gtk_entry_set_has_frame (GTK_ENTRY (entry->entry), FALSE);
	gtk_box_pack_start (GTK_BOX (priv->hbox), entry->entry, TRUE, TRUE, /* FIXME */ 0);

	/* We need to queue a redraw when focus changes, to comply with themes
	 * (like Clearlooks) which draw focused and unfocused entries differently.
	 */
	g_signal_connect_after (entry->entry, "focus-in-event",
				G_CALLBACK (entry_focus_change_cb), entry);
	g_signal_connect_after (entry->entry, "focus-out-event",
				G_CALLBACK (entry_focus_change_cb), entry);
}

static void
ephy_icon_entry_realize (GtkWidget *widget)
{
	GdkWindowAttr attributes;
	gint attributes_mask;
	gint border_width;
	GtkAllocation widget_allocation;
	GdkWindow *window;

	gtk_widget_set_realized (widget, TRUE);

	border_width = gtk_container_get_border_width (GTK_CONTAINER (widget));

	gtk_widget_get_allocation (widget, &widget_allocation);

	attributes.x = widget_allocation.x + border_width;
	attributes.y = widget_allocation.y + border_width;
	attributes.width = widget_allocation.width - 2 * border_width;
	attributes.height = widget_allocation.height - 2 * border_width;
	attributes.window_type = GDK_WINDOW_CHILD;
	attributes.event_mask = gtk_widget_get_events (widget)
				| GDK_EXPOSURE_MASK;

	attributes.visual = gtk_widget_get_visual (widget);
	attributes.colormap = gtk_widget_get_colormap (widget);
	attributes.wclass = GDK_INPUT_OUTPUT;
	attributes_mask = GDK_WA_X | GDK_WA_Y | GDK_WA_VISUAL | GDK_WA_COLORMAP;

	window = gdk_window_new (gtk_widget_get_parent_window (widget),
					 &attributes, attributes_mask);
	gtk_widget_set_window (widget, window);

	gdk_window_set_user_data (window, widget);

	gtk_widget_style_attach (widget);

	gtk_style_set_background (gtk_widget_get_style (widget),
            window, GTK_STATE_NORMAL);
}

static void
ephy_icon_entry_size_request (GtkWidget *widget,
			      GtkRequisition *requisition)
{
	EphyIconEntry *entry = EPHY_ICON_ENTRY (widget);
	GtkContainer *container = GTK_CONTAINER (widget);
	GtkBin *bin = GTK_BIN (widget);
	int xborder, yborder;
	GtkWidget *child;

	requisition->width = requisition->height = gtk_container_get_border_width (container) * 2;

	gtk_widget_ensure_style (entry->entry);
	ephy_icon_entry_get_borders (widget, entry->entry, &xborder, &yborder);

	child = gtk_bin_get_child (bin);

	if (gtk_widget_get_visible (child))
	{
		GtkRequisition child_requisition;

		gtk_widget_size_request (child, &child_requisition);
		requisition->width += child_requisition.width;
		requisition->height += child_requisition.height;
	}

	requisition->width += 2 * xborder;
	requisition->height += 2 * yborder;
}

static void
ephy_icon_entry_size_allocate (GtkWidget *widget,
			       GtkAllocation *allocation)
{
	EphyIconEntry *entry = EPHY_ICON_ENTRY (widget);
	GtkContainer *container = GTK_CONTAINER (widget);
	GtkBin *bin = GTK_BIN (widget);
	GtkAllocation child_allocation;
	GtkRequisition requisition;
	int xborder, yborder;
	guint container_border_width;
	GtkAllocation widget_allocation;

	gtk_widget_set_allocation (widget, allocation);
	container_border_width = gtk_container_get_border_width (container);

	ephy_icon_entry_get_borders (widget, entry->entry, &xborder, &yborder);

	if (gtk_widget_get_realized (widget))
	{
		child_allocation.x = container_border_width;
		child_allocation.y = container_border_width;
		child_allocation.width = MAX (allocation->width - container_border_width * 2, 0);
		child_allocation.height = MAX (allocation->height - container_border_width * 2, 0);

		gdk_window_move_resize (gtk_widget_get_window (widget),
					allocation->x + child_allocation.x,
					allocation->y + child_allocation.y,
					child_allocation.width,
					child_allocation.height);
	}
  
	gtk_widget_get_child_requisition (widget, &requisition);

	gtk_widget_get_allocation (widget, &widget_allocation);

	child_allocation.x = container_border_width + xborder;
	child_allocation.y = container_border_width + yborder
	  + (widget_allocation.height - requisition.height) / 2;
	child_allocation.width = MAX (allocation->width - (container_border_width + xborder) * 2, 0);
	child_allocation.height = MAX (allocation->height - (container_border_width + yborder) * 2, 0);

	/* We have to set the size requisition on the GtkEntry explicitly,
	 * since otherwise it'll end up too tall if someone uses
	 * gtk_widget_set_size_request on this EphyIconEntry,
	 * because gtk_entry_size_allocate checks its size with
	 * gtk_widget_get_child_requisition.
	 */
	gtk_widget_set_size_request (entry->entry, -1, child_allocation.height);

	gtk_widget_size_allocate (gtk_bin_get_child (bin), &child_allocation);
}

static gboolean
ephy_icon_entry_expose (GtkWidget *widget,
			GdkEventExpose *event)
{
	if (gtk_widget_is_drawable (widget) &&
	    event->window == gtk_widget_get_window (widget))
	{
		ephy_icon_entry_paint (widget, event);
	}

	return parent_class->expose_event (widget, event);
}

static void
ephy_icon_entry_class_init (EphyIconEntryClass *klass)
{
	GObjectClass *object_class = G_OBJECT_CLASS (klass);
	GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

	parent_class = GTK_WIDGET_CLASS (g_type_class_peek_parent (klass));

	widget_class->realize = ephy_icon_entry_realize;
	widget_class->size_request = ephy_icon_entry_size_request;
	widget_class->size_allocate = ephy_icon_entry_size_allocate;
	widget_class->expose_event = ephy_icon_entry_expose;

	g_type_class_add_private (object_class, sizeof (EphyIconEntryPrivate));
}

GType
ephy_icon_entry_get_type (void)
{
	static GType type = 0;

	if (G_UNLIKELY (type == 0))
	{
		static const GTypeInfo our_info =
		{
			sizeof (EphyIconEntryClass),
			NULL,
			NULL,
			(GClassInitFunc) ephy_icon_entry_class_init,
			NULL,
			NULL,
			sizeof (EphyIconEntry),
			0,
			(GInstanceInitFunc) ephy_icon_entry_init
		};

		type = g_type_register_static (GTK_TYPE_BIN,
					       "EphyIconEntry",
					       &our_info, 0);
	}

	return type;
}

/* public functions */

GtkWidget *
ephy_icon_entry_new (void)
{
	return GTK_WIDGET (g_object_new (EPHY_TYPE_ICON_ENTRY, NULL));
}

void
ephy_icon_entry_pack_widget (EphyIconEntry *entry,
			     GtkWidget *widget,
			     gboolean start)
{
	EphyIconEntryPrivate *priv;

	g_return_if_fail (EPHY_IS_ICON_ENTRY (entry));

	priv = entry->priv;

	if (start)
	{
		gtk_box_pack_start (GTK_BOX (priv->hbox), widget, FALSE, FALSE, /* FIXME */ 2);
		gtk_box_reorder_child (GTK_BOX (priv->hbox), widget, 0);
	}
	else
	{
		gtk_box_pack_end (GTK_BOX (priv->hbox), widget, FALSE, FALSE, /* FIXME */ 2);
	}
}

GtkWidget *
ephy_icon_entry_get_entry (EphyIconEntry *entry)
{
	g_return_val_if_fail (EPHY_IS_ICON_ENTRY (entry), NULL);

	return entry->entry;
}
