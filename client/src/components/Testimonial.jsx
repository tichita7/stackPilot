import React from "react";

const testimonial = [
  {
    text: "StackPilot helped us move faster without sacrificing design quality. The components feel production-ready.",
    name: "Cristofer Levin",
    role: "Frontend engineer",
    image:
      "https://images.unsplash.com/photo-1633332755192-727a05c4013d?q=80&w=200",
  },
  {
    text: "The attention to detail in StackPilot is impressive. Saved me hours of repetitive work and time. Highly recommended.",
    name: "Rohan Mehta",
    role: "Startup founder",
    image:
      "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?q=80&w=200",
  },
  {
    text: "We were able ship faster using StackPilot. The consistency across components made UI feel polished.",
    name: "Jason Kim",
    role: "Product designer",
    image: "https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=200",
  },
  {
    text: "StackPilot feels like it was built by people who actually ship products. Components are clean and easy to use.",
    name: "Alex Turner",
    role: "Full stack developer",
    image: "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=200",
  },
  {
    text: "StackPilot helped us maintain design consistency across multiple projects. It's now a core part of design.",
    name: "Sofia Martinez",
    role: "UX designer",
    image:
      "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=100",
  },
  {
    text: "Our team productivity improved noticeably after adopting StackPilot. It reduced design handoff friction.",
    name: "Daniel Wong",
    role: "UI designer",
    image:
      "https://raw.githubusercontent.com/prebuiltui/prebuiltui/main/assets/userImage/userImage1.png",
  },
];

const TestimonialCard = ({ testimonial }) => (
  <div className="bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-4 shrink-0 w-[350px]">
    <div className="flex mb-4">
      {Array(5)
        .fill(0)
        .map((_, i) => (
          <svg
            key={i}
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-transparent fill-[#737373]"
          >
            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z" />
          </svg>
        ))}
    </div>
    <p className="text-neutral-700 text-sm mb-6">{testimonial.text}</p>
    <div className="flex items-center gap-3">
      <img
        src={testimonial.image}
        alt={testimonial.name}
        className="w-11 h-11 rounded-full object-cover"
      />
      <div>
        <p className="font-medium text-neutral-800 text-sm">
          {testimonial.name}
        </p>
        <p className="text-neutral-600 text-sm">{testimonial.role}</p>
      </div>
    </div>
  </div>
);

const Testimonial = () => {
  const row1 = testimonial.slice(0, 3);
  const row2 = testimonial.slice(3, 6);

  return (
    <section className="bg-[#FAFAFA] py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <div className="inline-block bg-neutral-100 border border-neutral-400 rounded-full px-4 py-1 mb-3">
            <span className="text-xs text-neutral-600">Loved by clients</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-medium text-neutral-900 mb-4">
            What people are saying
          </h2>
          <p className="text-neutral-600 text-sm max-w-96 mx-auto">
            Real feedback from founders, developers and teams building
            production-ready products.
          </p>
        </div>

        <div className="space-y-6">
          {/* Row 1 - scrolls left */}
          <div className="relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-28 bg-gradient-to-r from-[#FAFAFA] to-transparent z-10 pointer-events-none"></div>
            <div className="absolute right-0 top-0 bottom-0 w-28 bg-gradient-to-l from-[#FAFAFA] to-transparent z-10 pointer-events-none"></div>
            <div className="flex gap-6 animate-scroll">
              {[...row1, ...row1].map((t, i) => (
                <TestimonialCard key={i} testimonial={t} />
              ))}
            </div>
          </div>

          {/* Row 2 - scrolls right */}
          <div className="relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-28 bg-gradient-to-r from-[#FAFAFA] to-transparent z-10 pointer-events-none"></div>
            <div className="absolute right-0 top-0 bottom-0 w-28 bg-gradient-to-l from-[#FAFAFA] to-transparent z-10 pointer-events-none"></div>
            <div className="flex gap-6 animate-scroll-reverse">
              {[...row2, ...row2].map((t, i) => (
                <TestimonialCard key={i} testimonial={t} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Testimonial;
