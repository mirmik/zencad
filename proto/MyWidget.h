#ifndef MY_WIDGET_H
#define MY_WIDGET_H

#include <QtWidgets>

class MyWidget : public QWidget {
	Q_OBJECT
public:

	QPushButton* button;
	QVBoxLayout* layout;

	MyWidget() {
		layout = new QVBoxLayout(this);
		button = new QPushButton(this);

		layout->addWidget(button);

		setLayout(layout);
	}
};

#endif